"""Cross-lane correlation: for each hang and top-N worst hitches, aggregate
Time Profiler samples and SwiftUI updates whose timestamps fall inside the
event window [start, start+duration]. Uses bisect so lookups stay O(log N)
per event.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from typing import Any


def build(lanes: dict[str, dict], top_hitches: int = 5, top_symbols: int = 5) -> list[dict]:
    """Produce a list of correlation entries.

    `lanes` is a dict keyed by lane name (time-profiler, hangs, hitches,
    swiftui) of their analyzer outputs.
    """
    tp = lanes.get("time-profiler")
    hangs = lanes.get("hangs")
    hitches = lanes.get("hitches")
    swiftui = lanes.get("swiftui")

    tp_index = _build_time_profile_index(tp)
    sui_events = (swiftui or {}).get("_events") if swiftui and swiftui.get("available") else None
    sui_index = _process_indexes(sui_events, "start_ns") if sui_events is not None else None

    correlations: list[dict] = []

    if hangs and hangs.get("available"):
        for h in hangs.get("_events", []):
            correlations.append(
                _correlate_event(
                    trigger_lane="hangs",
                    start_ns=h["start_ns"],
                    end_ns=h["end_ns"],
                    process=(h.get("thread") or {}).get("process"),
                    extra={"hang_type": h["hang_type"]},
                    tp_index=tp_index,
                    sui_index=sui_index,
                    top_symbols=top_symbols,
                )
            )

    if hitches and hitches.get("available"):
        worst_hitches = hitches.get("_events", [])[:top_hitches]
        for hi in worst_hitches:
            correlations.append(
                _correlate_event(
                    trigger_lane="hitches",
                    start_ns=hi["start_ns"],
                    end_ns=hi["end_ns"],
                    process=hi.get("process_identity") or {"name": hi.get("process")},
                    extra={
                        "frame_duration_ms": hi["frame_duration_ms"],
                        "hitch_duration_ms": hi["hitch_duration_ms"],
                    },
                    tp_index=tp_index,
                    sui_index=sui_index,
                    top_symbols=top_symbols,
                )
            )

    return correlations


# --- Internal -------------------------------------------------------------

def _build_time_profile_index(tp: dict | None):
    if not tp or not tp.get("available"):
        return None
    samples = tp.get("_samples") or []
    if not samples:
        return None
    return _process_indexes(samples, "time_ns")


def _process_indexes(events: list[dict], time_key: str) -> dict:
    by_pid: dict[int, list] = defaultdict(list)
    by_name: dict[str, list] = defaultdict(list)
    for event in events:
        identity = event.get("process_identity") or {"name": event.get("process")}
        if identity.get("pid") is not None:
            by_pid[identity["pid"]].append(event)
        if identity.get("name"):
            by_name[identity["name"]].append(event)
    def index(rows):
        rows = sorted(rows, key=lambda row: row[time_key])
        return {"times": [row[time_key] for row in rows], "samples": rows}
    return {"by_pid": {key: index(rows) for key, rows in by_pid.items()},
            "by_name": {key: index(rows) for key, rows in by_name.items()}}


def _select_process(indexes: dict, process: dict | None):
    """Never infer the trigger's process from whichever samples happen to overlap."""
    process = process or {}
    if process.get("pid") is not None:
        index = indexes["by_pid"].get(process["pid"])
    elif process.get("name"):
        index = indexes["by_name"].get(process["name"])
        if index:
            pids = {(row.get("process_identity") or {}).get("pid")
                    for row in index["samples"]}
            if len(pids) > 1:
                return None, "process name maps to multiple or unidentified process instances"
    else:
        return None, "trigger process identity is unavailable"
    if index is None:
        return None, "no samples with a matching process identity are available"
    return index, None


def _correlate_event(
    trigger_lane: str,
    start_ns: int,
    end_ns: int,
    process: dict | None,
    extra: dict,
    tp_index: dict | None,
    sui_index: dict | None,
    top_symbols: int,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "trigger": {
            "lane": trigger_lane,
            "start_ms": round(start_ns / 1_000_000, 2),
            "end_ms": round(end_ns / 1_000_000, 2),
            "duration_ms": round((end_ns - start_ns) / 1_000_000, 2),
            **extra,
            "process": process,
        },
    }

    notes = []
    selected_index, reason = (_select_process(tp_index, process)
                              if tp_index is not None else (None, None))
    if selected_index is not None:
        tp = _time_profile_hot_symbols(
            selected_index, start_ns, end_ns, top_symbols
        )
        duration_ns = end_ns - start_ns
        # Estimate using a 1ms/sample interval. The recording may use another
        # interval or omit samples; low coverage alone does not prove blocking.
        expected_if_running = max(1, duration_ns // 1_000_000)
        coverage_pct = min(100.0, 100.0 * tp["samples_main"] / expected_if_running)
        entry["time_profiler_main_thread"] = {
            "samples_in_window": tp["samples_total"],
            "samples_on_main": tp["samples_main"],
            "main_running_coverage_pct": round(coverage_pct, 1),
            "coverage_assumption": "1ms/sample; sampling coverage alone does not establish blocking",
            "hot_symbols": tp["hot_symbols"],
        }
    elif reason:
        notes.append(f"Time Profiler correlation unavailable: {reason}.")

    if sui_index is not None:
        selected_sui, reason = _select_process(sui_index, process)
        if selected_sui is not None:
            entry["swiftui_overlapping_updates"] = _swiftui_overlaps(
                selected_sui["samples"], start_ns, end_ns)
        else:
            notes.append(f"SwiftUI correlation unavailable: {reason}.")
    if notes:
        entry["notes"] = notes

    return entry


def _time_profile_hot_symbols(
    tp_index: dict, start_ns: int, end_ns: int, top_n: int
) -> dict:
    """Return main-thread hot symbols in the given window.

    Hang/hitch/SwiftUI correlations are all main-thread responsiveness
    problems, so worker-thread symbols are noise. We also return a coverage
    metric. Sparse samples may warrant inspecting waits, recording settings
    or dropped data; they cannot by themselves distinguish those causes.
    """
    times = tp_index["times"]
    samples = tp_index["samples"]
    lo = bisect_left(times, start_ns)
    hi = bisect_right(times, end_ns)
    window = samples[lo:hi]
    if not window:
        return {"samples_total": 0, "samples_main": 0, "hot_symbols": []}

    main_samples = [s for s in window if s["is_main"]]
    weight_by_symbol: dict[str, int] = defaultdict(int)
    count_by_symbol: dict[str, int] = defaultdict(int)
    for s in main_samples:
        weight_by_symbol[s["leaf_symbol"]] += s["weight_ns"]
        count_by_symbol[s["leaf_symbol"]] += 1
    total_weight = sum(weight_by_symbol.values()) or 1

    ranked = sorted(weight_by_symbol.items(), key=lambda kv: kv[1], reverse=True)
    hot = []
    for symbol, weight in ranked[:top_n]:
        hot.append({
            "symbol": symbol,
            "samples": count_by_symbol[symbol],
            "weight_ms": round(weight / 1_000_000, 2),
            "percent_of_main": round(100.0 * weight / total_weight, 2),
        })
    return {
        "samples_total": len(window),
        "samples_main": len(main_samples),
        "hot_symbols": hot,
    }


def _swiftui_overlaps(
    events: list[dict], start_ns: int, end_ns: int
) -> list[dict]:
    # Events aren't guaranteed sorted by start_ns here (we sort by duration in
    # swiftui.analyze). Linear scan; SwiftUI event counts are typically small.
    out: list[dict] = []
    for e in events:
        if e["end_ns"] < start_ns or e["start_ns"] > end_ns:
            continue
        out.append({
            "view": e["view"],
            "duration_ms": e["duration_ms"],
            "start_ms": e["start_ms"],
        })
    # Worst first.
    out.sort(key=lambda x: x["duration_ms"], reverse=True)
    return out[:10]
