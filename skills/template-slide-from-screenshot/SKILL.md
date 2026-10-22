---
name: template-slide-from-screenshot
description: Replicate a PowerPoint template slide (provided as a screenshot) inside this repo's WBR/QBR PPTX report generator using python-pptx. Use when the user shares a template slide image and asks to match its style, charts, or layout in the generated deck, or to add/redo a cybersecurity (VM / IAM / SecOps / SMC) slide.
disable-model-invocation: true
---

# Template Slide From Screenshot

Match a template slide (given as a screenshot) in the generated PPTX deck. The
generator builds slides **programmatically with python-pptx** — there is no
master template file you can copy from, so you recreate the look with shapes,
charts, tables, and direct chart-XML label injection.

## Where everything lives

| Concern | Path |
|---|---|
| Cyber slide builders (`_build_*`, `build_cyber_section`) | `backend/app/services/qbr_pptx/cyber_pptx.py` |
| Shared helpers (`_new_slide`, `_set_layout_title`, `_add_table`, `_add_text`, `_add_rect`, `_add_bar_chart`, `LAYOUT_TITLE_ONLY`) | `backend/app/services/qbr_pptx/slides.py` |
| Theme: colors, fonts, slide geometry | `backend/app/services/qbr_pptx/theme.py` |
| PPTX entry + wiring (`generate_qbr_pptx`, `cyber_data` param) | `backend/app/services/qbr_pptx/export.py` |
| Excel parsers (one per source file) | `backend/app/services/cybersecurity_import/parsers/*.py` |
| Data-type enum (`ImportFileType`) | `backend/app/enums/wbr.py` |
| Slide-type enum, titles, order (`WbrSlideType`, `SLIDE_TITLES`, `DEFAULT_SLIDE_ORDER`) | `backend/app/enums/wbr_presentation.py` |
| Web-UI markdown (NOT the PPTX) | `backend/app/services/qbr_pptx/cyber_slides.py` |

**Critical: two separate pipelines.** `cyber_slides.py` produces markdown for the
web UI editor. The actual `.pptx` is built only by the `_build_*` functions in
`cyber_pptx.py`, dispatched from `build_cyber_section()` → `export.generate_qbr_pptx`.
Editing the markdown does NOT change the deck. Always edit `cyber_pptx.py`.

## Workflow

1. **Identify the slide + data source.** Map the template screenshot to a
   `_build_*` function and a `cyber_data` key (`ImportFileType.*.value`). If it's
   a brand-new slide, see "Adding a new slide" below.

2. **Inspect the real parsed data** before designing. Run the verify snippet
   (below) against the actual Excel in `/Users/vpidborsky001/Downloads/Cybersecurity/`.
   Confirm the data has what the template shows AND that it is the *current* week:
   - Workbooks often contain stale summary tabs and months of history columns.
     Scan all sheets and pick the one with the **most date columns** (latest),
     then **trim to the last N weeks** the template shows (e.g. 5).
   - openpyxl returns dates as `datetime` OR strings — normalize with
     `strftime("%-d-%b")` (e.g. "18-May").

3. **Decide chart/table type per region** of the template (see "Chart playbook").

4. **Implement** the `_build_*` function using the helpers and the geometry
   constants. Keep every shape above the footer.

5. **Verify programmatically.** There is **no LibreOffice on this machine**, so
   you cannot render to an image. Render one slide to `/tmp` and inspect it with
   `scripts/inspect_pptx.py` (chart types, series, label counts, bounding boxes,
   footer-overflow flags). Do NOT claim it "looks right" — verify structure.

6. **Hand off for visual review.** Tell the user to regenerate the deck and send
   a screenshot, then iterate. Builder-only changes need NO re-import; parser
   changes DO require re-import (or add a builder-side safety net — step 2).

7. **Update `CHANGELOG.md`** (this repo requires it for every shipped change).
   Cyber slide changes are user-visible → `### Added`/`### Improved`.

## Chart playbook (lessons that matter)

- **Normalization vs proportional bars.** When values span huge ranges (e.g. 65
  vs 1,831 devices) real proportional bars make small ones invisible. Two fixes:
  - *Equal-height*: give every bar a fixed unit value (e.g. `1.0`); show real
    numbers only via labels.
  - *Baseline + fraction*: set the reference series to `1.0` and others to
    `value/total`, so you compare the *ratio* per category.
  Only normalize when the template does. The coverage/health and category-issues
  slides are normalized; the SMC investigations/severity charts use **real**
  proportional values (the template does).

- **Custom per-point labels** → use `_add_series_labels(series, labels, size=,
  color=, pos=)` in `cyber_pptx.py`. It injects chart XML (`c:dLbl`) because
  python-pptx's built-in `data_labels` can't do per-point multi-line custom text.
  `pos="ctr"` (inside, for stacked/equal bars) or `pos="outEnd"` (above bars).
  `"\n"` in a label renders stacked lines (e.g. `"89.5%\n16.5k"`).

- **Stacked coverage/health** → `_add_coverage_chart_labeled(...)`: 2 visible
  segments (managed + unmanaged) at fixed heights, a zero-height legend-only
  "Coverage %" series, hidden value axis, % + count overlaid as labels.

- **Clustered comparison** → `XL_CHART_TYPE.COLUMN_CLUSTERED`, color series
  `(NAVY, TEAL, TEAL_LIGHT)`, labels via `_add_series_labels`.

- **Single-series column / line** → `_simple_column_chart` / `_simple_line_chart`
  in `cyber_pptx.py` (no legend, value labels, optional hidden axis; line uses
  `LINE_MARKERS` with label `pos=ABOVE`).

- **Section header bands** → `_section_band(slide, y, text)` (full-width teal
  band, white bold title) for multi-region template slides like SMC.

- **Manual-input placeholders** → `_observation_box` (teal header + empty
  bullets) and `_comments_box` (grey panel). Templates often have narrative the
  source files don't contain — render an editable placeholder, never invent text.

- **Tables** → `_add_table(...)` returns the table (or `None`). Compact rows
  (~0.18–0.22"/row), set explicit cell font sizes, and **cap height below the
  footer**: `min(_FOOTER - top - margin, per_row*n + header)` to avoid the
  footer overlap that long tables cause.

## Geometry & theme

From `cyber_pptx.py` (Inches): `_TOP=1.35`, `_LEFT=0.55`, `_HALF_W=5.9`,
`_RIGHT=7.0`, `_FULL_W=SLIDE_WIDTH-1.1`, `_FOOTER=7.15`. Slide is 13.333×7.5.
Title via `_set_layout_title(slide, LAYOUT_TITLE_ONLY, title)`; titles come from
`SLIDE_TITLES[WbrSlideType.X]` + `" — {week_label}"`.

Theme (`theme.py`): `NAVY`, `TEAL`, `TEAL_LIGHT`, `GREY`, `ORANGE`, `LIGHT`
(cream), `WHITE`; fonts `FONT_TITLE` ("Franklin Gothic Medium"), `FONT_BODY`
("Arial"). Chart-XML colors need hex strings (e.g. NAVY = `"002339"`).

Every `_build_*` must handle missing data: `if not payload: _no_data_slide(...)`.

## Adding a new slide (not just restyling)

1. `ImportFileType` value in `app/enums/wbr.py` + a parser in
   `cybersecurity_import/parsers/` + persist via the repository.
2. `WbrSlideType` + `SLIDE_TITLES` entry + add to `DEFAULT_SLIDE_ORDER` in
   `app/enums/wbr_presentation.py`.
3. Write `_build_<slide>(prs, cyber_data, week_label)` in `cyber_pptx.py`.
4. Call it inside `build_cyber_section()`.
5. `CHANGELOG.md`.

## Verify one slide without the app

Render a single builder against the real Excel, then inspect structure:

```python
import sys; sys.path.insert(0, "backend")
import openpyxl
from pptx import Presentation
from app.services.wbr_import.loader.workbook_snapshot import WorkbookSnapshot
from app.enums.wbr import ImportFileType
from app.services.qbr_pptx import cyber_pptx
# 1) pick the source workbook + its parser + data key + builder
f = "/Users/vpidborsky001/Downloads/Cybersecurity/SecOps/Sentinel one Agent Category issues Summary weekly.xlsx"
from app.services.cybersecurity_import.parsers.s1_category_issues import parse_s1_category_issues as parse
key, build = ImportFileType.CYBER_S1_CATEGORY.value, cyber_pptx._build_s1_category_issues
# 2) load → snapshot → parse → build
raw = openpyxl.load_workbook(f, data_only=True)
sheets = {n: tuple(tuple(r) for r in raw[n].iter_rows(values_only=True)) for n in raw.sheetnames}
wb = WorkbookSnapshot(source_name="t.xlsx", sheets=sheets)
prs = Presentation()
build(prs, {key: parse(wb)}, "Week of May 31, 2026")
prs.save("/tmp/_one.pptx")
```

Then: `python .cursor/skills/template-slide-from-screenshot/scripts/inspect_pptx.py /tmp/_one.pptx`

Run from repo root with the backend venv active (`source backend/.venv/bin/activate`).

## Anti-patterns

- Editing `cyber_slides.py` expecting the PPTX to change (wrong pipeline).
- Claiming success from code alone — inspect structure + get a user screenshot.
- Inventing narrative/observations the source files don't contain.
- Forgetting that DB data predates parser fixes (re-import or add a builder-side trim).
- Letting tables or bands cross `_FOOTER` (7.15").
- Skipping the `CHANGELOG.md` update.
