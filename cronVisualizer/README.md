# Cron Schedule Visualizer

An interactive Python tool for visualizing cron job schedules with dark mode graphics. This tool generates a clickable monthly calendar view with detailed daily timeline visualizations showing exactly when your cron jobs execute. Click on a day or the weekly view link to generate more detailed views.

## Features

- **Interactive Monthly Calendar**: Click on any day or on week view to see detailed execution patterns
- **Pixel-Perfect Daily Timelines**: 24hrs x 60min = 1440px wide images where 1 pixel = 1 minute
- **Week View**: Stack 7 days vertically for week-at-a-glance visualization
- **Dark Mode Theme**: Modern, consistent dark color scheme throughout
- **Multiple Cron Jobs**: Support for multiple cron expressions separated by `|`
- **Thumbnail Previews**: Mini timeline previews in calendar cells
- **Execution Visualization**: Bright green execution bars for maximum visibility
- **Time Labels**: Dual time format (24-hour and AM/PM)
- **Human-Readable Descriptions**: Convert cron syntax to plain English

## Screenshots

The tool generates three types of visualizations:

1. **Monthly Calendar View**: Interactive calendar with thumbnail previews
2. **Daily Timeline View**: 1440px wide detailed timeline (1 pixel = 1 minute)
3. **Week View**: 7 daily timelines stacked vertically

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows OS (uses `os.startfile()` for opening images)

### Install Dependencies

```bash
pip install pandas seaborn matplotlib pillow numpy
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

### Requirements File

If you prefer to use a requirements.txt file, create one with:

```txt
pandas>=1.3.0
seaborn>=0.11.0
matplotlib>=3.5.0
pillow>=8.0.0
numpy>=1.21.0
```

## Usage

### Basic Usage

```python
from main import generate_monthly_calendar

# Simple cron job - every 15 minutes during business hours
cron_string = "*/15 9-17 * * *"
generate_monthly_calendar(cron_string, year=2025, month=6)
```

### Advanced Usage

```python
# Multiple cron jobs separated by |
cron_string = "3-10 0-4,18-23 * * * | */15 10-22 * * * | 27 14 1-3,15 * *"
generate_monthly_calendar(cron_string, year=2025, month=6)
```

### Running the Script

```bash
cd cronVisualizer
python main.py
```

## Cron Expression Format

The tool supports standard cron expressions with 5 fields:

```
minute hour dayOfMonth month dayOfWeek
```

### Supported Syntax

- `*` - Any value
- `*/n` - Every n units
- `n-m` - Range from n to m
- `n,m,p` - Specific values
- Multiple jobs: `job1 | job2 | job3`

### Examples

```python
# Every 15 minutes during business hours
"*/15 9-17 * * *"

# 4 times a day at specific hours
"0 9,12,15,18 * * *"

# 2:30 PM on 1st and 15th of every month
"27 14 1,15 * *"

# Midnight every Sunday
"0 0 * * 0"

# Complex multi-job example
"3-10 0-4,18-23 * * * | */15 10-22 * * * | 27 14 1-3,15 * *"
```

## Output Files

The tool generates PNG files in the current directory:

- `cron_calendar_X.png` - Monthly calendar view
- `daily_timeline_YYYY-MM-DD.png` - Daily timeline view
- `week_view_YYYY-MM_weekX.png` - Week view
- `debug_daily_YYYY-MM-DD.png` - Debug timeline (raw)


## Dependencies Explained


- **pandas**: Data manipulation and calendar matrix creation
- **seaborn**: Statistical plotting enhancements
- **matplotlib**: Interactive plotting and calendar visualization
- **pillow (PIL)**: Image creation and text rendering
- **numpy**: Array operations for timeline data
- **calendar**: Built-in Python calendar utilities
- **datetime**: Date and time manipulation

## Troubleshooting

### Common Issues

1. **Image won't open**: Make sure you're on Windows (uses `os.startfile()`)
2. **Font errors**: The tool falls back to default font if arial.ttf is not found
3. **Missing dependencies**: Install all required packages with pip
4. **Large output files**: Timeline images are intentionally high resolution

### Performance Notes

- Large cron expressions may take a moment to process
- Image files are optimized for precision over file size
- Calendar generation is fast, timeline rendering takes more time
