---
name: template-slide-from-screenshot
description: Match a screenshot in a python-pptx WBR/QBR report generator, with an applicability-checked cybersecurity project adapter. Use when the user shares a slide screenshot and wants to reproduce its layout, charts or style in a generated PPTX.
disable-model-invocation: true
---

# Template Slide From Screenshot

Match the supplied screenshot in the user's actual PPTX generator. Discover the repository, generator, data source, reusable theme/helpers and available rendering tools first. Preserve an existing template/master workflow when one exists; do not assume every deck is generated from shapes.

The paths and helpers below describe a particular WBR/QBR cybersecurity adapter. Apply them only after finding the matching files and confirming their current responsibilities. In another repository, map these responsibilities to its own code or use the available presentation skill. Do not create this project structure just because it appears here.

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

**For the verified adapter: two separate pipelines.** `cyber_slides.py` produces markdown for the
web UI editor. The actual `.pptx` is built only by the `_build_*` functions in
`cyber_pptx.py`, dispatched from `build_cyber_section()` → `export.generate_qbr_pptx`.
Editing that markdown does not change the deck. Confirm the actual PPTX dispatch path before editing its builder.

## Workflow

1. **Identify the slide + data source.** Map the template screenshot to a
   `_build_*` function and a `cyber_data` key (`ImportFileType.*.value`). If it's
   a brand-new slide, see "Adding a new slide" below.

2. **Inspect the actual parsed data** before designing. Use the workbook supplied by the user or verified project configuration; never assume another machine's Downloads path. Confirm the requested reporting period and the source fields required by the screenshot.
   - Summary tabs and historical columns can be stale. Parse date headers/cells, compare their actual reporting dates and applicable data coverage, and select the sheet that covers the requested period. More date columns does not mean newer data. Sort normalized dates before selecting the requested last N weeks; flag future/ambiguous dates and conflicting sheets.
   - Normalize workbook `datetime` and supported string formats explicitly. Reject or clarify ambiguous dates instead of guessing. Format display labels portably (for example, `f"{date.day}-{date:%b}"`); `%-d` is not portable to every operating system.

3. **Decide chart/table type per region** of the template (see "Chart playbook").

4. **Implement** the `_build_*` function using the helpers and the geometry
   constants. Keep every shape above the footer.

5. **Verify at the requested level.** Discover available presentation renderers and project checks rather than assuming LibreOffice is absent. When verification is authorized, generate an isolated sample deck; resolve `scripts/inspect_pptx.py` from this loaded skill directory to inspect chart types, labels, bounds and footer overflow. Structural inspection does not prove visual fidelity.

6. **Review the visual output** with an available renderer when authorized. If rendering is unavailable, report that limit and request a screenshot only when needed for further iteration. In the verified adapter, builder-only changes normally do not require data re-import; parser changes may require it. Do not silently change stored user data as a fallback.

7. **Follow the project's changelog convention** when shipping a user-visible change. Do not assume every repository uses the same sections or version scheme.

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

For the verified adapter, confirm these values in the current `cyber_pptx.py` before using them (Inches): `_TOP=1.35`, `_LEFT=0.55`, `_HALF_W=5.9`,
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
f = "<verified-workbook-path>"
from app.services.cybersecurity_import.parsers.s1_category_issues import parse_s1_category_issues as parse
key, build = ImportFileType.CYBER_S1_CATEGORY.value, cyber_pptx._build_s1_category_issues
# 2) load → snapshot → parse → build
raw = openpyxl.load_workbook(f, data_only=True)
sheets = {n: tuple(tuple(r) for r in raw[n].iter_rows(values_only=True)) for n in raw.sheetnames}
wb = WorkbookSnapshot(source_name="t.xlsx", sheets=sheets)
prs = Presentation()
build(prs, {key: parse(wb)}, "Week of May 31, 2026")
prs.save("<isolated-output-directory>/one-slide.pptx")
```

Then run `python3 "<loaded-skill-directory>/scripts/inspect_pptx.py" "<isolated-output-directory>/one-slide.pptx"`.

The snippet is an adapter example, not a universal runnable command. Run only after verifying its imports, source fields, reporting period and environment. Use the project's actual Python interpreter/environment; do not assume a backend virtual environment path.

## Anti-patterns

- Editing `cyber_slides.py` expecting the PPTX to change (wrong pipeline).
- Claiming visual fidelity from structural checks alone — inspect a rendered slide or disclose the rendering limit.
- Inventing narrative/observations the source files don't contain.
- Forgetting that DB data predates parser fixes (re-import or add a builder-side trim).
- Letting tables or bands cross `_FOOTER` (7.15").
- Ignoring the verified project's changelog policy.
