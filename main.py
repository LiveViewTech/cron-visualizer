# --- Utility: get_execution_times for a single cron string ---
def get_execution_times(cron_expr, year, month, day):
    """
    Returns a sorted list of minutes since midnight for all executions on this day for a single cron string.
    Uses check_cron_matches_date to get (hour, minute) tuples.
    """
    times = check_cron_matches_date(cron_expr, year, month, day)
    return sorted([h * 60 + m for h, m in times])
#!/usr/bin/env python3
"""
Hello World - Main Python File
A simple hello world program for the cronScheduleVisualizer project.
"""

import pandas as pd
import seaborn as sns
import matplotlib
# Configure matplotlib backend for headless systems (servers without display)
# This must be done before importing pyplot
try:
    import tkinter
    matplotlib.use('TkAgg')  # Use TkAgg backend if tkinter is available
except ImportError:
    matplotlib.use('Agg')  # Use Agg backend for headless systems

import matplotlib.pyplot as plt
import calendar
from datetime import datetime
import os
import platform
import subprocess

# Color constants for execution visualization
EXECUTION_COLOR_RGB = [0, 255, 0]  # Bright green for execution bars
EXECUTION_COLOR_HEX = '#00FF00'     # Bright green for thumbnails

# Dark mode color constants
DARK_BACKGROUND_RGB = [30, 30, 30]     # Dark gray background
DARK_BACKGROUND_HEX = '#1E1E1E'        # Dark gray background for thumbnails
GRID_LINE_COLOR = [80, 80, 80]         # Medium gray for grid lines
QUARTER_LINE_COLOR = [60, 60, 60]      # Darker gray for 15-minute lines
TEXT_COLOR = (220, 220, 220)           # Light gray for text (tuple for PIL)

# Additional color constants for remaining hard-coded colors
FIGURE_BACKGROUND_HEX = '#1E1E1E'      # Dark background for matplotlib figure
CALENDAR_GRID_COLOR = '#505050'        # Medium gray for calendar grid lines
THUMBNAIL_BACKGROUND_HEX = '#404040'   # Lighter gray background for calendar thumbnails
WEEK_BUTTON_COLOR = '#4A9EFF'          # Light blue for week view buttons
CALENDAR_TEXT_WHITE = 'white'          # White text for calendar
CALENDAR_TEXT_LIGHT_GRAY = 'lightgray' # Light gray text for calendar
AM_PM_TEXT_COLOR = (160, 160, 160)     # Medium gray for AM/PM labels (tuple for PIL)

def open_image_cross_platform(filename):
    """
    Open an image file using the default application on Windows, macOS, and Linux.
    """
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(filename)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", filename])
        elif system == "Linux":
            subprocess.run(["xdg-open", filename])
        else:
            print(f"   ⚠️  Unknown operating system: {system}")
            print(f"   📁 Please manually open: {filename}")
            return False
        return True
    except Exception as e:
        print(f"   ⚠️  Could not open image: {e}")
        print(f"   📁 Please manually open: {filename}")
        return False

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
    import datetime
    
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
        days_of_week = parse_cron_part(parts[4], 0, 6)  # 0=Sunday, 1=Monday, ..., 6=Saturday
        
        # Get the day of week for this date (0=Monday, 1=Tuesday, ..., 6=Sunday in Python)
        date_obj = datetime.date(year, month, day)
        python_weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
        
        # Convert Python weekday to cron weekday (0=Sunday, 1=Monday, ..., 6=Saturday)
        cron_weekday = (python_weekday + 1) % 7  # Convert: Mon(0)->1, Tue(1)->2, ..., Sun(6)->0
        
        # Check if this date matches the cron criteria
        # Both day of month AND day of week must match (if specified)
        day_of_month_matches = (parts[2] == '*') or (day in days_of_month)
        day_of_week_matches = (parts[4] == '*') or (cron_weekday in days_of_week)
        month_matches = month in months
        
        # In cron, if both day of month and day of week are specified (not '*'), 
        # the job runs if EITHER matches (OR logic), not both (AND logic)
        if parts[2] != '*' and parts[4] != '*':
            # Both specified - use OR logic
            day_matches = day_of_month_matches or day_of_week_matches
        else:
            # At least one is '*' - use AND logic
            day_matches = day_of_month_matches and day_of_week_matches
        
        if month_matches and day_matches:
            job_execution_times = [(hour, minute) for hour in hours for minute in minutes]
            all_execution_times.extend(job_execution_times)
    
    # Remove duplicates (in case multiple cron jobs schedule the same time)
    return list(set(all_execution_times))

def show_daily_view(jobs, year, month, day):
    """Show detailed daily view for a specific date"""
    import numpy as np
    from matplotlib.colors import ListedColormap
    from PIL import Image

    # Build a 1D timeline: 1440 pixels wide, 1 pixel = 1 minute
    timeline = np.zeros(1440, dtype=np.uint8)
    execution_times = []
    for job in jobs:
        cron_expr = job['cron']
        # get_execution_times returns a list of minutes since midnight
        times = get_execution_times(cron_expr, year, month, day)
        for t in times:
            if 0 <= t < 1440:
                timeline[t] = 1
        execution_times.extend(times)

    # Create a display image that's exactly 1440px wide with embedded labels and title
    date_str = f"{year}-{month:02d}-{day:02d}"
    display_height = 200  # Increased height for title, timeline, labels, and bottom padding
    display_array = np.full((display_height, 1440, 3), DARK_BACKGROUND_RGB, dtype=np.uint8)  # Dark background
    
    # Copy the timeline to the display image (centered vertically)
    timeline_height = 40
    timeline_y_start = 80  # Lower to make room for title
    timeline_y_end = timeline_y_start + timeline_height
    
    # First draw the grid lines (background layer)
    # Add hour grid lines directly to the image array (extend moderately above/below)
    for hour in range(0, 25):
        x = hour * 60
        if x < 1440:
            # Draw vertical grid line - dark mode colors
            line_color = GRID_LINE_COLOR  # Medium gray grid lines
            line_width = 1
            
            # Draw the vertical line extending further above and below than 15-minute lines
            for w in range(line_width):
                if x + w < 1440:
                    display_array[timeline_y_start-15:timeline_y_end+15, x+w] = line_color
    
    # Add 15-minute graduation lines (extend less than hour lines)
    for quarter in range(24 * 4 + 1):  # Include the final mark at 24:00
        x = quarter * 15
        if x < 1440 and x % 60 != 0:  # Skip hour marks (they're already drawn above)
            # Draw lighter 15-minute graduation lines that extend less than hour lines
            line_color = QUARTER_LINE_COLOR  # Dark gray for 15-minute lines
            line_width = 1
            
            # Extend 8 pixels above and below the timeline (less than hour lines)
            for w in range(line_width):
                if x + w < 1440:
                    display_array[timeline_y_start-8:timeline_y_end+8, x+w] = line_color
    
    # Finally, draw the execution bars on top of everything (foreground layer)
    # This ensures execution pixels are never hidden by grid lines in the middle
    for minute in range(1440):
        if timeline[minute] == 1:
            # Execution color for executions
            display_array[timeline_y_start:timeline_y_end, minute] = EXECUTION_COLOR_RGB
    
    # Add simple text labels using basic pixel drawing (hour numbers)
    # We'll draw simple hour numbers below the timeline
    from PIL import Image, ImageDraw, ImageFont
    
    # Convert to PIL Image to add text, then back to array
    pil_image = Image.fromarray(display_array)
    draw = ImageDraw.Draw(pil_image)
    
    try:
        # Try to use a system font, fall back to default if not available
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Add title at the top
    title_text = f"Cron Schedule Timeline - {date_str} (1440px = 24 hours, 1 pixel = 1 minute)"
    title_bbox = draw.textbbox((0, 0), title_text, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (1440 - title_width) // 2  # Center the title
    draw.text((title_x, 10), title_text, fill=TEXT_COLOR, font=font)
    
    # Add hour labels below the timeline (both 24-hour and AM/PM format)
    for hour in range(0, 25):  # Every hour to show all hour marks
        x = hour * 60
        if x < 1440:
            # 24-hour format (remove leading zeros and :00)
            hour_24 = str(hour)
            text_bbox = draw.textbbox((0, 0), hour_24, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            # Position hour labels - center all labels on their hour lines
            if hour == 0:
                text_x = 2  # Fixed position near left edge for "0"
            else:  # All other hours get centered positioning
                text_x = max(10, x - text_width // 2)
            
            text_y = timeline_y_end + 25
            # Use same font size for all hour labels
            draw.text((text_x, text_y), hour_24, fill=TEXT_COLOR, font=font)
            
            # AM/PM format below the 24-hour format - only for even hours to avoid crowding
            if hour % 2 == 0:
                if hour == 0:
                    hour_ampm = "12 AM"
                elif hour == 12:
                    hour_ampm = "12 PM"
                elif hour < 12:
                    hour_ampm = f"{hour} AM"
                else:
                    hour_ampm = f"{hour-12} PM"
                
                text_bbox = draw.textbbox((0, 0), hour_ampm, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                # Special handling for hour 0 - move it further left
                if hour == 0:
                    text_x = 2  # Fixed position near left edge for "12 AM"
                else:
                    text_x = max(10, x - text_width // 2)  # Center on hour line, but ensure minimum 10px from left edge
                text_y = timeline_y_end + 45
                draw.text((text_x, text_y), hour_ampm, fill=AM_PM_TEXT_COLOR, font=font)
    
    # Convert back to numpy array
    display_array = np.array(pil_image)
    
    # Save the final display image that's exactly 1440px wide
    display_filename = f"daily_timeline_{date_str}.png"
    Image.fromarray(display_array).save(display_filename)
    
    # Timeline creation complete
    print(f"\n🎯 SUCCESS: PIXEL-PERFECT TIMELINE CREATED!")
    print(f"   📁 {display_filename} (1440×{display_height}px)")
    print(f"   ✅ Exactly 1440px wide (1 pixel = 1 minute)")
    print(f"   🔍 Open the PNG file for precise measurements!")
    
    # Display the exact image using PIL's built-in viewer (TRUE 1:1 pixels!)
    print(f"\n📺 OPENING PIXEL-PERFECT IMAGE VIEWER...")
    print(f"   Opening: {display_filename}")
    print(f"   This shows EXACT 1:1 pixel mapping (no stretching!)")
    print(f"   Each pixel = 1 minute, 1440px = 24 hours")
    
    try:
        # Open the image directly from project directory (cross-platform)
        if open_image_cross_platform(display_filename):
            print(f"   ✅ Daily view opened from project directory!")
        
    except Exception as e:
        print(f"   ⚠️  Could not open image viewer: {e}")
        print(f"   📁 Please manually open: {display_filename}")
        print(f"   🔍 Any image viewer will show true 1:1 pixels!")
    
    # Also create a simple text summary for the terminal
    print(f"\n📊 EXECUTION SUMMARY for {date_str}:")
    print(f"   Total executions: {len(execution_times)}")
    if execution_times:
        first_execution = min(execution_times)
        last_execution = max(execution_times)
        first_hour, first_min = divmod(first_execution, 60)
        last_hour, last_min = divmod(last_execution, 60)
        print(f"   First execution: {first_hour:02d}:{first_min:02d} (minute {first_execution})")
        print(f"   Last execution:  {last_hour:02d}:{last_min:02d} (minute {last_execution})")
        
        # Show execution distribution by hour
        hour_counts = {}
        for minute in execution_times:
            hour = minute // 60
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        print(f"   Executions by hour:")
        for hour in sorted(hour_counts.keys()):
            count = hour_counts[hour]
            bar = "█" * min(count, 20)  # Simple text bar chart
            print(f"     {hour:02d}:xx - {count:3d} times {bar}")
    else:
        print(f"   No executions scheduled for this day.")
    
    # Add job descriptions below the plot
    descriptions = [describe_cron_schedule(job['cron']) for job in jobs]
    desc_text = '\n'.join(descriptions)
    if desc_text:
        print(f"\nJob descriptions:\n{desc_text}")

def show_week_view(jobs, year, month, week_data):
    """Show a week view with all 7 days stacked vertically"""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    
    # Constants for the week view
    day_height = 180  # Increased height per day timeline to accommodate labels below
    total_width = 1440  # Same as daily view for consistency
    week_height = 7 * day_height + 100  # 7 days plus margins
    
    # Create the week image
    week_array = np.full((week_height, total_width, 3), DARK_BACKGROUND_RGB, dtype=np.uint8)  # Dark background
    
    # Day names for labels
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_idx in range(7):
        day_num = week_data[day_idx] if day_idx < len(week_data) else 0
        
        if day_num > 0:  # Valid day
            # Calculate vertical position for this day
            y_start = day_idx * day_height + 50
            timeline_y_start = y_start + 30
            timeline_height = 40
            timeline_y_end = timeline_y_start + timeline_height
            
            # Get execution times for this day
            execution_times = check_cron_matches_date(
                ' | '.join([job['cron'] for job in jobs]), year, month, day_num
            )
            
            # Create timeline for this day
            timeline = np.zeros(1440, dtype=np.uint8)
            for hour, minute in execution_times:
                absolute_minute = hour * 60 + minute
                if 0 <= absolute_minute < 1440:
                    timeline[absolute_minute] = 1
            
            # Draw grid lines for this day (background layer) - same as daily view
            # Add hour grid lines directly to the image array (extend moderately above/below)
            for hour in range(0, 25):
                x = hour * 60
                if x < 1440:
                    # Draw vertical grid line - dark mode colors
                    line_color = GRID_LINE_COLOR  # Medium gray grid lines
                    line_width = 1
                    
                    # Draw the vertical line extending further above and below than 15-minute lines
                    for w in range(line_width):
                        if x + w < 1440:
                            week_array[timeline_y_start-15:timeline_y_end+15, x+w] = line_color
            
            # Add 15-minute graduation lines (extend less than hour lines)
            for quarter in range(24 * 4 + 1):  # Include the final mark at 24:00
                x = quarter * 15
                if x < 1440 and x % 60 != 0:  # Skip hour marks (they're already drawn above)
                    # Draw lighter 15-minute graduation lines that extend less than hour lines
                    line_color = QUARTER_LINE_COLOR  # Dark gray for 15-minute lines
                    line_width = 1
                    
                    # Extend 8 pixels above and below the timeline (less than hour lines)
                    for w in range(line_width):
                        if x + w < 1440:
                            week_array[timeline_y_start-8:timeline_y_end+8, x+w] = line_color
            
            # Finally, draw the execution bars on top of everything (foreground layer)
            # This ensures execution pixels are never hidden by grid lines in the middle
            for minute in range(1440):
                if timeline[minute] == 1:
                    # Execution color for executions
                    week_array[timeline_y_start:timeline_y_end, minute] = EXECUTION_COLOR_RGB
    
    # Convert to PIL Image to add text labels
    pil_image = Image.fromarray(week_array)
    draw = ImageDraw.Draw(pil_image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Add title
    week_start_day = next((day for day in week_data if day > 0), 1)
    week_end_day = max((day for day in week_data if day > 0), default=week_start_day)
    title_text = f"Week View: {calendar.month_name[month]} {week_start_day}-{week_end_day}, {year}"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (total_width - title_width) // 2
    draw.text((title_x, 10), title_text, fill=TEXT_COLOR, font=title_font)
    
    # Add day labels and hour markers
    for day_idx in range(7):
        day_num = week_data[day_idx] if day_idx < len(week_data) else 0
        
        if day_num > 0:
            y_start = day_idx * day_height + 50
            timeline_y_start = y_start + 30
            timeline_y_end = timeline_y_start + 40
            
            # Day label on the left - positioned well above timeline and gridlines
            day_label = f"{day_names[day_idx]} {day_num}"
            draw.text((10, timeline_y_start - 25), day_label, fill=TEXT_COLOR, font=font)
            
            # Hour labels (every hour to match daily view) - positioned below grid lines
            for hour in range(0, 25):  # Every hour to show all hour marks
                x = hour * 60
                if x < 1440:
                    # 24-hour format (no leading zeros)
                    hour_24 = str(hour)
                    text_bbox = draw.textbbox((0, 0), hour_24, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    
                    # Position hour labels - center all labels on their hour lines (same as daily view)
                    if hour == 0:
                        text_x = 2  # Fixed position near left edge for "0" (same as daily view)
                    else:  # All other hours get centered positioning (same as daily view)
                        text_x = max(10, x - text_width // 2)
                    
                    text_y = timeline_y_end + 30
                    # Use same font size for all hour labels
                    draw.text((text_x, text_y), hour_24, fill=TEXT_COLOR, font=font)
                    
                    # AM/PM format below the 24-hour format - only for even hours to avoid crowding
                    if hour % 2 == 0:
                        if hour == 0:
                            hour_ampm = "12 AM"
                        elif hour == 12:
                            hour_ampm = "12 PM"
                        elif hour < 12:
                            hour_ampm = f"{hour} AM"
                        else:
                            hour_ampm = f"{hour-12} PM"
                        
                        text_bbox = draw.textbbox((0, 0), hour_ampm, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        # Position AM/PM labels same as daily view
                        if hour == 0:
                            text_x = 2  # Fixed position near left edge for "12 AM" (same as daily view)
                        else:
                            text_x = max(10, x - text_width // 2)  # Center on hour line, but ensure minimum 10px from left edge (same as daily view)
                        text_y = timeline_y_end + 50
                        draw.text((text_x, text_y), hour_ampm, fill=AM_PM_TEXT_COLOR, font=font)
    
    # Save the week view image
    week_filename = f"week_view_{year}-{month:02d}_week{week_data[0] if week_data[0] > 0 else 'X'}.png"
    pil_image.save(week_filename)
    
    print(f"\n📅 WEEK VIEW CREATED!")
    print(f"   📁 {week_filename}")
    print(f"   📊 7 daily timelines stacked vertically")
    print(f"   🔍 Each timeline: 1440px wide, 1 pixel = 1 minute")
    
    # Open the week view image directly from project directory (cross-platform)
    try:
        if open_image_cross_platform(week_filename):
            print(f"   ✅ Week view opened from project directory!")
    except Exception as e:
        print(f"   ⚠️  Could not open week view: {e}")
        print(f"   📁 Please manually open: {week_filename}")
    
    # Print week summary
    total_executions = 0
    for day_idx in range(7):
        day_num = week_data[day_idx] if day_idx < len(week_data) else 0
        if day_num > 0:
            execution_times = check_cron_matches_date(
                ' | '.join([job['cron'] for job in jobs]), year, month, day_num
            )
            day_count = len(execution_times)
            total_executions += day_count
            print(f"   {day_names[day_idx]} {day_num}: {day_count} executions")
    
    print(f"   Total week executions: {total_executions}")

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
    
    # Parse cron string into jobs format for the daily view
    cron_jobs = cron_string.split(' | ')
    jobs = [{'cron': job.strip()} for job in cron_jobs]
    
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
    fig, ax = plt.subplots(figsize=(15, 8))  # Slightly wider to accommodate week view buttons
    fig.patch.set_facecolor(FIGURE_BACKGROUND_HEX)  # Dark background for figure
    ax.set_facecolor(FIGURE_BACKGROUND_HEX)  # Dark background for axes
    
    # Create a blank calendar grid instead of heatmap - extend to include week view buttons
    ax.set_xlim(-1, 7)  # Extended left margin for week view buttons
    ax.set_ylim(0, len(cal_matrix))
    ax.set_aspect('equal')
    
    # Draw grid lines with dark mode colors
    for i in range(len(cal_matrix) + 1):
        ax.axhline(i, color=CALENDAR_GRID_COLOR, linewidth=1)
    for j in range(8):
        ax.axvline(j, color=CALENDAR_GRID_COLOR, linewidth=1)
    
    # Add week view links on the left of each row (simple hyperlink style)
    week_buttons = []  # Store text areas for click detection
    for i in range(len(cal_matrix)):
        week_y = len(cal_matrix) - i - 0.5
        
        # Simple hyperlink-style text positioning
        text_x = -0.5
        text_y = week_y
        
        # Add hyperlink-style text with underline
        week_text = ax.text(text_x, text_y, 'Week View', 
                           fontsize=9, ha='center', va='center', 
                           color=WEEK_BUTTON_COLOR, style='italic')  # Light blue for dark mode
        
        # Add underline by drawing a line below the text
        # Calculate approximate text width and position
        text_width = 0.5  # Approximate width for "Week View"
        line_y = week_y - 0.08  # Slightly below the text
        ax.plot([text_x - text_width/2, text_x + text_width/2], [line_y, line_y], 
               color=WEEK_BUTTON_COLOR, linewidth=0.8, alpha=0.8)  # Light blue for dark mode
        
        # Store text area info for click detection (wider area for easier clicking)
        click_width = 0.7
        click_height = 0.3
        week_buttons.append({
            'rect': (text_x - click_width/2, text_y - click_height/2, click_width, click_height),
            'week_index': i,
            'week_data': cal_matrix[i]
        })
    
    # Add daily view thumbnails for days with jobs
    for i in range(len(cal_matrix)):
        for j in range(7):
            if j < len(cal_matrix[i]):
                day_num = cal_matrix[i][j]
                if day_num > 0:  # Valid day of month
                    day_str = str(day_num)
                    
                    if day_num in events:
                        # Day has events - create scaled-down thumbnail preview
                        execution_times = check_cron_matches_date(cron_string, year, month, day_num)
                        
                        # Create a scaled-down version of the 1440-minute timeline
                        # Use higher resolution: 288 pixels wide (5 minutes per pixel) for better accuracy
                        import numpy as np
                        thumbnail_width = 288  # 5 minutes per pixel for better resolution
                        thumbnail_height = 3   # Thinner height for more accurate representation
                        thumb_array = np.zeros((thumbnail_height, thumbnail_width))
                        
                        for hour, minute in execution_times:
                            # Convert hour:minute to absolute minute, then compress by 5
                            absolute_minute = hour * 60 + minute
                            thumbnail_pixel = min(absolute_minute // 5, thumbnail_width - 1)
                            thumb_array[:, thumbnail_pixel] = 1  # Fill all rows
                        
                        # Draw the thumbnail within the calendar cell
                        cell_padding = 0.05
                        cell_width = 0.9
                        cell_height = 0.6
                        cell_x = j + cell_padding
                        cell_y = len(cal_matrix) - i - 0.85

                        # Create extent for imshow (left, right, bottom, top)
                        extent = [cell_x, cell_x + cell_width,
                                 cell_y, cell_y + cell_height]

                        # Construct date_obj for this day
                        date_obj = datetime(year, month, day_num)
                        # Display the thumbnail as a single image
                        from matplotlib.colors import ListedColormap
                        cmap = ListedColormap([THUMBNAIL_BACKGROUND_HEX, EXECUTION_COLOR_HEX])  # Lighter background, execution color for executions
                        ax.imshow(thumb_array, extent=extent, aspect='auto',
                                 cmap=cmap, alpha=0.9, origin='lower', interpolation='bilinear')

                        # Add day number below the thumbnail
                        ax.text(j + 0.5, len(cal_matrix) - i - 0.15, day_str, 
                               color=CALENDAR_TEXT_WHITE, fontsize=9, ha="center", va="center", 
                               fontweight="bold")
                    else:
                        # Day exists but no events - just show day number
                        ax.text(j + 0.5, len(cal_matrix) - i - 0.5, day_str, 
                               color=CALENDAR_TEXT_LIGHT_GRAY, fontsize=12, ha="center", va="center", 
                               fontweight="bold")
    
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
            ha='center', va='bottom', fontsize=16, fontweight='bold', color=CALENDAR_TEXT_WHITE)
    
    # Add the field labels (small, positioned to align with cron string)
    ax.text(0.5, 1.10, 'minute hour dayOfMonth month dayOfWeek', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=9, style='italic', color=CALENDAR_TEXT_LIGHT_GRAY)
    
    # Add the description (medium)
    ax.text(0.5, 1.05, f'{cron_description} - {calendar.month_name[month]} {year}', 
            transform=ax.transAxes, ha='center', va='bottom', fontsize=12, color=CALENDAR_TEXT_WHITE)
    
    # Add the instruction (small)
    ax.text(0.5, 1.00, 'Click on a day for detailed 1440-pixel timeline view (1 pixel = 1 minute). Click "Week View" buttons for 7-day stack view. Thumbnails show daily patterns.', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=10, style='italic', color=CALENDAR_TEXT_LIGHT_GRAY)
    
    # Set up the calendar labels
    ax.set_xticks([i + 0.5 for i in range(7)])
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], color=CALENDAR_TEXT_WHITE)
    ax.set_yticks([])
    ax.set_yticklabels([])
    
    # Remove default spines and add custom border
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Add outer border for the entire calendar (excluding week buttons)
    border = plt.Rectangle((0, 0), 7, len(cal_matrix), fill=False, 
                          edgecolor=CALENDAR_TEXT_WHITE, linewidth=2)
    ax.add_patch(border)
    
    # Add click event handler
    def on_click(event):
        if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
            # Check if click is on a week view button
            for button_info in week_buttons:
                bx, by, bw, bh = button_info['rect']
                if (bx <= event.xdata <= bx + bw and 
                    by <= event.ydata <= by + bh):
                    # Week button clicked
                    print(f"Week view button clicked for week {button_info['week_index'] + 1}")
                    show_week_view(jobs, year, month, button_info['week_data'])
                    return  # Early return prevents day cell processing
            
            # Check if click is on a day cell
            if event.xdata >= 0 and event.xdata < 7:
                col = int(event.xdata)
                row = int(event.ydata)
                
                # Ensure we're within bounds and account for matplotlib's coordinate system
                if 0 <= row < len(cal_matrix) and 0 <= col < 7:
                    # Convert matplotlib row to calendar matrix row (flip y-axis)
                    calendar_row = len(cal_matrix) - 1 - row
                    if 0 <= calendar_row < len(cal_matrix) and col < len(cal_matrix[calendar_row]):
                        day = cal_matrix[calendar_row][col]
                        if day > 0:  # Valid day
                            show_daily_view(jobs, year, month, day)
    
    fig.canvas.mpl_connect('button_press_event', on_click)
    
    plt.tight_layout()
    
    # Save the calendar
    counter = 1
    while os.path.exists(f"cron_calendar_{counter}.png"):
        counter += 1
    filename = f"cron_calendar_{counter}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor=FIGURE_BACKGROUND_HEX)
    
    plt.show()
    print(f"Interactive calendar saved as '{filename}'")

def describe_cron_schedule(cron_string):
    """
    Generate a human-readable description of a cron schedule.
    Similar to crontab.guru descriptions.
    Handles multiple cron jobs separated by '|'.
    """
    # Handle multiple cron jobs separated by '|'
    cron_jobs = [job.strip() for job in cron_string.split('|')]
    
    if len(cron_jobs) > 1:
        # Multiple jobs - describe each one
        descriptions = []
        for i, job in enumerate(cron_jobs, 1):
            job_desc = describe_single_cron_job(job)
            if job_desc != "Invalid cron format":
                descriptions.append(f"Job {i}: {job_desc}")
        
        if descriptions:
            return " | ".join(descriptions)
        else:
            return "Invalid cron format"
    else:
        # Single job
        return describe_single_cron_job(cron_jobs[0])

def describe_single_cron_job(cron_string):
    """
    Generate a human-readable description of a single cron job.
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
    
    # Day of week
    weekday_desc = ""
    if weekday_part != '*':
        weekday_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        if ',' in weekday_part:
            days = [weekday_names[int(d)] for d in weekday_part.split(',')]
            weekday_desc = f"on {', '.join(days[:-1])}, and {days[-1]}"
        elif '-' in weekday_part:
            start, end = map(int, weekday_part.split('-'))
            if start == 1 and end == 5:
                weekday_desc = "on weekdays (Monday through Friday)"
            elif start == 0 and end == 6:
                weekday_desc = "every day"
            else:
                start_name = weekday_names[start]
                end_name = weekday_names[end]
                weekday_desc = f"on {start_name} through {end_name}"
        else:
            weekday_desc = f"on {weekday_names[int(weekday_part)]}"
    
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
        # When minute is specified but hour is *, we want "Every hour at X minutes"
        if time_desc:
            description_parts.append(f"Every hour {time_desc[0]}")
        else:
            description_parts.append("Every hour")
    else:
        description_parts.extend(time_desc)
    
    if day_desc:
        description_parts.append(day_desc)
    if weekday_desc:
        description_parts.append(weekday_desc)
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
    # "27 14 1,15 * *"           # 2:27 PM on 1st and 15th of every month
    # "0 0 * * 0"                # Midnight every Sunday
    
    cron_string = "* 0-5,18-23 * * 1-5 | * * * * 0,6"  # A complicated example: "3-10 0-4,18-23 * * * | */15 10-22 * * * | 27 14 1-3,15 * *"

    print("=== Interactive Cron Schedule Visualizer ===")
    print("Monthly calendar view with clickable daily details")
    print()
    
    # You can specify a different year/month, or leave None for current
    generate_monthly_calendar(cron_string, year=None, month=None)

if __name__ == "__main__":
    main()

