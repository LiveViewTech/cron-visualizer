#!/usr/bin/env python3
"""
Hello World - Main Python File
A simple hello world program for the cronScheduleVisualizer project.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import calendar
from datetime import datetime
import os

def parse_cron_part(part_str, min_val, max_val):
    """
    Parses a single part of a cron string (like for minutes, hours, etc.).
    Handles '*', '*/n', 'n-m', 'n,m,p' syntaxes.
    """
    if part_str == '*':
        return list(range(min_val, max_val + 1))
    
    if '*/' in part_str:
        step = int(part_str.split('/')[1])
        return list(range(min_val, max_val + 1, step))

    if ',' in part_str:
        ranges = []
        for item in part_str.split(','):
            if '-' in item:
                start, end = map(int, item.split('-'))
                ranges.extend(list(range(start, end + 1)))
            else:
                ranges.append(int(item))
        return sorted(ranges)

    if '-' in part_str:
        start, end = map(int, part_str.split('-'))
        return list(range(start, end + 1))

    return [int(part_str)]

def check_cron_matches_date(cron_string, year, month, day):
    """
    Check if a cron job would execute on a specific date.
    Returns the list of (hour, minute) tuples for execution times on that date.
    Handles multiple cron strings separated by '|'.
    """
    all_execution_times = []
    
    # Split by '|' to handle multiple cron jobs
    cron_jobs = [job.strip() for job in cron_string.split('|')]
    
    for job in cron_jobs:
        parts = job.split()
        if len(parts) != 5:
            continue  # Skip invalid cron jobs

        minutes = parse_cron_part(parts[0], 0, 59)
        hours = parse_cron_part(parts[1], 0, 23)
        days_of_month = parse_cron_part(parts[2], 1, 31)
        months = parse_cron_part(parts[3], 1, 12)
        # Note: We're ignoring day of week (parts[4]) for simplicity
        
        # Check if this date matches the cron criteria
        if month in months and day in days_of_month:
            job_execution_times = [(hour, minute) for hour in hours for minute in minutes]
            all_execution_times.extend(job_execution_times)
    
    # Remove duplicates (in case multiple cron jobs schedule the same time)
    return list(set(all_execution_times))

def show_daily_view(cron_string, year, month, day):
    """
    Show the detailed daily 24x60 heatmap for a specific date.
    """
    execution_times = check_cron_matches_date(cron_string, year, month, day)
    
    if not execution_times:
        print(f"No cron jobs scheduled for {year}-{month:02d}-{day:02d}")
        return
    
    print(f"Showing daily view for {year}-{month:02d}-{day:02d}")
    print(f"Total execution times: {len(execution_times)}")
    
    # Create a DataFrame to represent the 24x60 grid of a day
    df = pd.DataFrame(0, index=range(24), columns=range(60))
    
    # Mark the execution times in the DataFrame
    for hour, minute in execution_times:
        df.loc[hour, minute] = 1
    
    # Create the heatmap in a new figure
    plt.figure(figsize=(16, 8))
    ax = sns.heatmap(df.T, cmap=["lightgrey", "#FF5733"], cbar=False, linewidths=.5, linecolor='white')
    
    # Customize the plot
    ax.set_title(f'Daily Cron Execution: {year}-{month:02d}-{day:02d} | "{cron_string}"', fontsize=14, pad=20)
    ax.set_xlabel('Hour of the Day', fontsize=12, labelpad=25)  # Added labelpad to move down
    ax.set_ylabel('Minute of the Hour', fontsize=12)
    
    # Set ticks to be more readable
    ax.set_xticks([i + 0.5 for i in range(24)])
    ax.set_xticklabels(range(24))
    
    # Add AM/PM labels below the 24-hour labels
    for i in range(24):
        if i == 0:
            ampm_label = "12 AM"
        elif i < 12:
            ampm_label = f"{i} AM"
        elif i == 12:
            ampm_label = "12 PM"
        else:
            ampm_label = f"{i-12} PM"
        
        ax.text(i + 0.5, 0, ampm_label, ha='center', va='bottom', 
                fontsize=8, color='gray', rotation=0)
    
    ax.set_yticks([i + 0.5 for i in range(0, 61, 5)])
    ax.set_yticklabels([f'{i:02}' for i in range(0, 61, 5)])
    
    # Don't invert y-axis - keep 0 at the top naturally
    # ax.invert_yaxis()  # Removed this line
    
    plt.tight_layout()
    plt.show()

def generate_monthly_calendar(cron_string, year=None, month=None):
    """
    Generate an interactive monthly calendar heatmap.
    Click on any day to see the detailed daily view.
    """
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
        
    print(f"Generating calendar for {calendar.month_name[month]} {year}")
    print(f"Cron string: {cron_string}")
    print("Click on any day to see detailed daily execution times!")
    
    # Parse cron to see which days have jobs
    events = {}  # Key: day_of_month, Value: count of execution times
    
    cal_matrix = calendar.monthcalendar(year, month)
    
    # Calculate execution times for each day of the month
    for week in cal_matrix:
        for day in week:
            if day > 0:  # Valid day of month
                execution_times = check_cron_matches_date(cron_string, year, month, day)
                if execution_times:
                    events[day] = len(execution_times)
    
    # Create DataFrames for heatmap
    heatmap_data = pd.DataFrame(cal_matrix, dtype=float).replace(0, float('nan'))
    day_labels = pd.DataFrame(cal_matrix).replace(0, '')
    
    # Populate the heatmap with event counts ONLY for days that have events
    # All other days should remain NaN (uncolored)
    for week_idx, week in enumerate(cal_matrix):
        for day_idx, day in enumerate(week):
            if day > 0:  # Valid day of month
                if day in events:
                    # Day has events - set the count
                    heatmap_data.iloc[week_idx, day_idx] = events[day]
                else:
                    # Day exists but no events - keep as NaN so it stays uncolored
                    heatmap_data.iloc[week_idx, day_idx] = float('nan')
    
    # Create the interactive plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use a color palette that shows intensity
    cmap = sns.light_palette("#2c7fb8", as_cmap=True)
    
    sns.heatmap(
        heatmap_data,
        cmap=cmap,
        annot=False,
        linewidths=1,  # Increased line width for more visible grid
        linecolor='lightgray',  # Changed to lighter gray
        cbar=True,
        cbar_kws={'label': 'Execution Count per Day'},
        ax=ax,
        square=True  # Make cells square-shaped
    )
    
    # Add day numbers
    for i in range(heatmap_data.shape[0]):
        for j in range(heatmap_data.shape[1]):
            if i < len(cal_matrix) and j < len(cal_matrix[i]):
                day_num = cal_matrix[i][j]
                if day_num > 0:  # Valid day of month
                    day_str = str(day_num)
                    # Choose text color: white if there are events, black if no events
                    text_color = "white" if pd.notna(heatmap_data.iloc[i, j]) else "black"
                    ax.text(j + 0.5, i + 0.5, day_str, color=text_color, 
                           fontsize=12, ha="center", va="center", fontweight="bold")
    
    # Set title and labels
    cron_description = describe_cron_schedule(cron_string)
    
    # Create multi-line title with different font sizes
    title_lines = [
        f'"{cron_string}"',
        'minute hour dayOfMonth month dayOfWeek',
        f'{cron_description} - {calendar.month_name[month]} {year}',
        'Click on a day for detailed view'
    ]
    
    ax.set_title('\n'.join(title_lines), fontsize=14, pad=20)
    
    # Manually adjust font sizes for different parts using text annotations
    # Remove the default title and add custom text
    ax.set_title('')  # Clear the title
    
    # Add the cron string (large)
    ax.text(0.5, 1.15, f'"{cron_string}"', transform=ax.transAxes, 
            ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Add the field labels (small, positioned to align with cron string)
    ax.text(0.5, 1.10, 'minute hour dayOfMonth month dayOfWeek', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=9, style='italic', color='gray')
    
    # Add the description (medium)
    ax.text(0.5, 1.05, f'{cron_description} - {calendar.month_name[month]} {year}', 
            transform=ax.transAxes, ha='center', va='bottom', fontsize=12)
    
    # Add the instruction (small)
    ax.text(0.5, 1.00, 'Click on a day for detailed view', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=10, style='italic')
    
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.set_yticklabels([])
    
    # Add outer border for the entire calendar
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)
        spine.set_edgecolor('black')
    
    # Add click event handler
    def on_click(event):
        if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
            col = int(event.xdata)
            row = int(event.ydata)
            
            if 0 <= row < len(cal_matrix) and 0 <= col < 7:
                day = cal_matrix[row][col]
                if day > 0:  # Valid day
                    show_daily_view(cron_string, year, month, day)
    
    fig.canvas.mpl_connect('button_press_event', on_click)
    
    plt.tight_layout()
    
    # Save the calendar
    counter = 1
    while os.path.exists(f"cron_calendar_{counter}.png"):
        counter += 1
    filename = f"cron_calendar_{counter}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    plt.show()
    print(f"Interactive calendar saved as '{filename}'")

def describe_cron_schedule(cron_string):
    """
    Generate a human-readable description of a cron schedule.
    Similar to crontab.guru descriptions.
    """
    parts = cron_string.split()
    if len(parts) != 5:
        return "Invalid cron format"
    
    minute_part, hour_part, day_part, month_part, weekday_part = parts
    
    # Helper function to describe time parts
    def describe_time_part(part, min_val, max_val, unit):
        if part == '*':
            return f"every {unit}"
        elif '/' in part:
            if part.startswith('*/'):
                step = part.split('/')[1]
                return f"every {step} {unit}s"
            else:
                return f"every {part.split('/')[1]} {unit}s"
        elif ',' in part:
            values = part.split(',')
            if len(values) == 2:
                return f"at {values[0]} and {values[1]}"
            else:
                return f"at {', '.join(values[:-1])}, and {values[-1]}"
        elif '-' in part:
            start, end = part.split('-')
            return f"from {start} through {end}"
        else:
            return f"at {part}"
    
    # Build description parts
    time_desc = []
    
    # Minutes
    if minute_part != '*':
        min_desc = describe_time_part(minute_part, 0, 59, "minute")
        time_desc.append(min_desc)
    
    # Hours  
    if hour_part != '*':
        hour_desc = describe_time_part(hour_part, 0, 23, "hour")
        if hour_part.isdigit():
            hour_val = int(hour_part)
            if hour_val == 0:
                hour_desc = "at midnight"
            elif hour_val == 12:
                hour_desc = "at noon"
            elif hour_val < 12:
                hour_desc = f"at {hour_val}:00 AM"
            else:
                hour_desc = f"at {hour_val-12}:00 PM"
        time_desc.append(hour_desc)
    
    # Day of month
    day_desc = ""
    if day_part != '*':
        if ',' in day_part:
            days = day_part.split(',')
            day_desc = f"on the {', '.join(days[:-1])}, and {days[-1]} of the month"
        elif '-' in day_part:
            start, end = day_part.split('-')
            day_desc = f"on days {start} through {end} of the month"
        else:
            day_desc = f"on the {day_part} of the month"
    
    # Month
    month_desc = ""
    if month_part != '*':
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        if month_part.isdigit():
            month_desc = f"in {month_names[int(month_part)]}"
        elif ',' in month_part:
            months = [month_names[int(m)] for m in month_part.split(',')]
            month_desc = f"in {', '.join(months[:-1])}, and {months[-1]}"
    
    # Combine all parts
    description_parts = []
    
    if minute_part == '*' and hour_part == '*':
        description_parts.append("Every minute")
    elif minute_part != '*' and hour_part == '*':
        description_parts.append(f"Every hour {time_desc[0]}")
    else:
        description_parts.extend(time_desc)
    
    if day_desc:
        description_parts.append(day_desc)
    if month_desc:
        description_parts.append(month_desc)
    
    return " ".join(description_parts)

def main():
    """
    Main function that creates an interactive monthly calendar heatmap.
    Click on any day to see the detailed daily execution pattern.
    """
    # Example cron strings to try:
    # "*/15 9-17 * * *"          # Every 15 minutes during business hours
    # "0 9,12,15,18 * * *"       # 4 times a day at specific hours
    # "30 14 1,15 * *"           # 2:30 PM on 1st and 15th of every month
    # "0 0 * * 0"                # Midnight every Sunday
    
    cron_string = "* 0-4,18-23 * * * | */15 10-22 * * *"  # Every 15 min, 9-5, on 1st and 15th of June
    
    print("=== Interactive Cron Schedule Visualizer ===")
    print("Monthly calendar view with clickable daily details")
    print()
    
    # You can specify a different year/month, or leave None for current
    generate_monthly_calendar(cron_string, year=2025, month=6)

if __name__ == "__main__":
    main()
