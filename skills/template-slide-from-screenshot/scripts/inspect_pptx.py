#!/usr/bin/env python3
"""Inspect a generated .pptx for structure and layout problems.

Because there is no LibreOffice on this machine to render slides to images,
use this to verify a slide programmatically: it lists every chart (type,
series, per-series custom-label count, bounding box) and every text/shape,
and flags any shape that crosses the footer line (7.15").

Usage:
    python inspect_pptx.py <file.pptx> [footer_inches]

Exit code is non-zero if any shape overflows the footer, so it doubles as a
cheap layout assertion in a verify loop.
"""

from __future__ import annotations

import sys

from pptx import Presentation
from pptx.util import Emu

FOOTER_DEFAULT = 7.15


def _in(emu) -> float:
    return round(Emu(emu).inches, 2)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python inspect_pptx.py <file.pptx> [footer_inches]")
        return 2
    path = sys.argv[1]
    footer = float(sys.argv[2]) if len(sys.argv) > 2 else FOOTER_DEFAULT

    prs = Presentation(path)
    overflow = 0

    for s_idx, slide in enumerate(prs.slides):
        print(f"\n=== Slide {s_idx} ===")
        for sh in slide.shapes:
            top, bottom = _in(sh.top), _in(sh.top + sh.height)
            left = _in(sh.left)
            crosses = bottom > footer
            flag = "  <-- OVERFLOWS FOOTER" if crosses else ""
            if crosses:
                overflow += 1

            if sh.has_chart:
                ch = sh.chart
                title = ch.chart_title.text_frame.text if ch.has_title else ""
                print(f" CHART {ch.chart_type} y={top}-{bottom} x={left} "
                      f"title={title!r}{flag}")
                for ser in ch.series:
                    n_lbl = ser._element.xml.count("<c:dLbl>")
                    print(f"     series {ser.name!r}: {n_lbl} custom labels")
                try:
                    print(f"     categories: {list(ch.plots[0].categories)}")
                except Exception:
                    pass
            elif sh.has_table:
                tbl = sh.table
                print(f" TABLE rows={len(tbl.rows)} cols={len(tbl.columns)} "
                      f"y={top}-{bottom} x={left}{flag}")
            elif sh.has_text_frame and sh.text_frame.text.strip():
                txt = sh.text_frame.text.strip().replace("\n", " ")[:50]
                print(f" TEXT  y={top}-{bottom} x={left} {txt!r}{flag}")
            else:
                print(f" SHAPE {sh.shape_type} y={top}-{bottom} x={left}{flag}")

    print(f"\nFooter line: {footer}\"  |  overflowing shapes: {overflow}")
    return 1 if overflow else 0


if __name__ == "__main__":
    raise SystemExit(main())
