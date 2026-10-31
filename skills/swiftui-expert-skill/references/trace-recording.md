# Recording an Instruments Trace

Use this reference when the user asks to record a new trace — either to
attach to a running app, launch one fresh, or capture a specific session
of actions they'll perform interactively.

The bundled `scripts/record_trace.py` wraps `xctrace record` with:

- The **SwiftUI** template by default (override with `--template`).
- **Manual stop** via Ctrl+C, a stop-file, or `--time-limit`.
- JSON discovery for devices and templates.
- Normal Python exit codes so an agent can orchestrate.
- Redacted command logging for values passed through `--env`.
- An explicit acknowledgement gate for system-wide recordings.

## Privacy and consent

Prefer `--attach` or `--launch`, which limits collection to the app being
diagnosed. A system-wide recording can capture activity and metadata from
unrelated applications. Before using `--all-processes`, explain that scope to
the user and obtain their explicit approval. Then pass
`--allow-system-wide-recording` to record that acknowledgement in the command.

Values passed through `--env KEY=VALUE` are forwarded to `xctrace`, but the
wrapper redacts each value from its displayed command. Avoid placing secrets on
command lines when a safer launch configuration is available, because other
local process-inspection tools may still expose process arguments.

## Typical flows

### A) Attach to a running app on a connected device

```bash
python3 "${SKILL_DIR}/scripts/record_trace.py" \
  --device "Pol's iPhone" \
  --attach "Helm" \
  --output ~/Desktop/helm-session.trace
```

Leave it running while the user exercises the app. Stop with **Ctrl+C**.

### B) Launch an app and record from the first frame

```bash
python3 "${SKILL_DIR}/scripts/record_trace.py" \
  --device "<UDID>" \
  --launch "/path/to/App.app" \
  --output ~/Desktop/launch.trace
```

Useful for diagnosing cold-start hitches and view-creation cost.

### C) Agent-driven: start in background, stop via stop-file

Use the host's background-process tool and a unique session marker. Before starting, create a new directory in the OS temporary area (for example with Python's `tempfile.mkdtemp`) and choose its `stop` child without creating that file. Retain the actual path in session state so a later tool call signals the same recording.

```bash
python3 "${SKILL_DIR}/scripts/record_trace.py" \
  --attach Helm --stop-file "<new-session-directory>/stop" \
  --output "<new-output-path>.trace"
```

When the user finishes, create exactly that marker with a file tool. A marker that already exists is stale input: allocate a new session path instead of deleting an unknown marker. The script polls for the marker and sends SIGINT to xctrace when it appears. Wait for recorder completion before analysing the output; remove only this session's marker/directory afterwards. Do not reuse a fixed `/tmp/stop-trace` path across recordings.

### D) Time-boxed recording

```bash
python3 "${SKILL_DIR}/scripts/record_trace.py" \
  --attach Helm --time-limit 30s --output ~/Desktop/30s.trace
```

xctrace stops itself at the limit.

## Discovery helpers

```bash
# List every connected device, simulator, and the host — JSON.
python3 "${SKILL_DIR}/scripts/record_trace.py" --list-devices

# List all Instruments templates — JSON with a flat list + by-section map.
python3 "${SKILL_DIR}/scripts/record_trace.py" --list-templates
```

Device entries have `kind` (`devices`, `devices offline`, `simulators`),
`name`, `os`, `udid`. Offline devices are known but unplugged / unpaired —
plug them in before recording.

## Picking a template

> **Hard rule: the `SwiftUI` template only populates the SwiftUI lane on a
> real device — a physical iOS/iPadOS device or the host Mac. On the iOS
> Simulator it records but the SwiftUI lane comes back empty.** If the
> chosen UDID falls under the `simulators` kind from `--list-devices`,
> switch to `Time Profiler`. It still gives you Time Profiler + Hangs +
> Animation Hitches, which `analyze_trace.py` analyses and correlates
> normally; only the `swiftui` lane will report `available: false`.

Decision flow:

| Target                                       | Template to pass     |
|----------------------------------------------|----------------------|
| Physical iOS/iPadOS device (connected)       | `SwiftUI` (default)  |
| Host Mac (macOS app, `--all-processes`, etc.)| `SwiftUI` (default)  |
| iOS / iPadOS / watchOS / tvOS Simulator      | `Time Profiler`      |

Always confirm the target kind with `--list-devices` before starting a
recording: entries under `simulators` mean you must switch to Time
Profiler; entries under `devices` (both connected devices and the host
Mac) support the SwiftUI template. Entries under `devices offline` need
the user to connect/unlock/trust the device before recording.

For ad-hoc hang hunting on any target, `Time Profiler` or
`Animation Hitches` alone may be enough.

For an explicitly approved system-wide recording:

```bash
python3 "${SKILL_DIR}/scripts/record_trace.py" \
  --all-processes --allow-system-wide-recording \
  --time-limit 30s --output ~/Desktop/system-wide.trace
```

## Chaining into analysis

Keep the explicit output path and recorder exit status rather than extracting a filename from combined log text. After a successful exit, verify the trace bundle exists and analyse that exact path:

```bash
python3 "${SKILL_DIR}/scripts/analyze_trace.py" \
  --trace "<verified-output-path>.trace" --json-only
```

A log message alone is not success evidence. If recording fails, report its status and preserve diagnostic output; do not analyse a stale bundle from an earlier session.

If the user wanted a specific scope, combine with `--list-logs` /
`--list-signposts` / `--window` from `references/trace-analysis.md`.

## Failure modes to handle

- **Device offline** — `--list-devices` shows it in `devices offline`.
  Ask the user to connect/unlock the device and retry.
- **Output path exists** — preserve the existing bundle and choose a new output path; deletion requires applicable user intent.
- **Stop marker already exists** — choose a fresh session directory/marker; do not remove a marker whose recording you do not own.
- **App not running (for `--attach`)** — xctrace exits with an error;
  fall back to `--launch` or tell the user to open the app first.
- **Signing / trust on device** — iOS requires a development build
  signed with the user's team. If xctrace returns a signing error, point
  the user to trust the developer profile on the device.
