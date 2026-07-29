# Cron Schedule Visualizer

## Purpose

Interactive Python tool that turns cron expressions into a clickable monthly calendar plus pixel-level daily and week timeline PNGs (1 pixel = 1 minute).

## Project Snapshot

- Tech: Python 3.7+, matplotlib, Pillow, pandas, numpy (seaborn listed but unused in `main.py`)
- Type: single-module script repo (no packages/, no CI, no tests)
- Entry: `main.py` → `main()` → `generate_monthly_calendar`
- Layout: flat root; no subdirectory `AGENTS.md` files

## Commands

```bash
pip install -r requirements.txt
python main.py
```

Library use (from `README.md`):

```python
from main import generate_monthly_calendar
generate_monthly_calendar("*/15 9-17 * * *", year=2025, month=6)
```

Edit the hardcoded `cron_string` in `main()` to change the demo schedule.

## Conventions

- Multi-job schedules: separate expressions with ` | ` (spaces around `|`). Prefer this form everywhere; `generate_monthly_calendar` splits on `' | '` while `check_cron_matches_date` / `describe_cron_schedule` split on `'|'`.
- Dark-mode colors: module-level RGB/HEX constants at top of `main.py` (`EXECUTION_COLOR_*`, `DARK_BACKGROUND_*`, etc.) — reuse these; do not hardcode new palette values in render paths.
- Daily timelines: 1440-wide arrays in `show_daily_view` / `show_week_view` (1 px = 1 minute).
- Matplotlib backend: TkAgg if tkinter exists, else Agg (`main.py` import block) — keep that order before `pyplot` import.
- Output PNGs land in CWD: `cron_calendar_N.png`, `daily_timeline_YYYY-MM-DD.png`, `week_view_YYYY-MM_weekX.png`.
- Cross-platform open: `open_image_cross_platform` — Windows `os.startfile`, macOS `open`, Linux `xdg-open`.

## Directory Map

- `main.py` — all parsing, calendar UI, daily/week PNG rendering
- `requirements.txt` — runtime deps
- `README.md` — usage, cron syntax, troubleshooting
- `.claude/repository-model.yaml` — structured repo intelligence model

## Architecture

1. `parse_cron_part` / `check_cron_matches_date` — expand cron fields; OR day-of-month vs day-of-week when both are non-`*`.
2. `generate_monthly_calendar` — matplotlib interactive grid, thumbnails, click → `show_daily_view` or `show_week_view`.
3. `describe_cron_schedule` / `describe_single_cron_job` — human-readable titles.

## Gotchas

- **Pipe splitter mismatch** in `main.py`: keep job separators consistent (`' | '` vs `'|'`).
- **Month/year boundaries** untested (see `README.md` troubleshooting) — do not assume week views spanning months are correct.
- **No automated tests or CI** — treat `parse_cron_part` / `check_cron_matches_date` changes as high-risk; verify manually with known cron strings.
- Font fallback: PIL tries `arial.ttf`, then default (`show_daily_view` / `show_week_view`).
- Module docstring at top of `main.py` still says "Hello World"; ignore it — `README.md` is authoritative.
