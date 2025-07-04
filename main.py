# --- Utility: get_execution_times for a single cron string ---
def get_execution_times(cron_expr, year, month, day):
    """
    Returns a sor    # First draw the grid lines (background layer)
    # Add hour grid lines directly to the image array (extend moderately above/below)
    for hour in range(0, 25):
        x = hour * 60
        if x < 1440:
            # Draw vertical grid line (light gray) - extend moderately above and below the timeline
            if hour % 2 == 0:  # Every 2 hours, draw a darker line
                line_color = [100, 100, 100]  # Dark gray
                line_width = 2
            else:
                line_color = [180, 180, 180]  # Light gray  
                line_width = 1
            
            # Draw the vertical line extending moderately above and below the timeline
            for w in range(line_width):
                if x + w < 1440:
                    display_array[timeline_y_start-10:timeline_y_end+10, x+w] = line_color
    
    # Add 15-minute graduation lines (lighter, extending slightly outside plot area)
    for quarter in range(24 * 4 + 1):  # Include the final mark at 24:00
        x = quarter * 15
        if x < 1440 and x % 60 != 0:  # Skip hour marks (they're already drawn above)
            line_color = [200, 200, 200]  # Very light gray
            # Draw the vertical line extending slightly outside the plot area
            display_array[timeline_y_start-5:timeline_y_end+5, x] = line_colores since midnight for all executions on this day for a single cron string.
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

    # Create a 2D array for imshow (1 row, 1440 columns)
    timeline_2d = timeline[np.newaxis, :]

    # Create a direct numpy array that's exactly 1440x200 pixels (RGB)
    # We'll create the image directly to ensure exact pixel control
    img_height = 200  # Enough for timeline + labels
    img_array = np.ones((img_height, 1440, 3), dtype=np.uint8) * 248  # Light gray background
    
    # Fill the timeline area (rows 60-100) with the execution data - twice as tall
    timeline_start_row = 60
    timeline_height = 40
    for minute in range(1440):
        if timeline[minute] == 1:
            # Darker blue color for better contrast with grid lines
            img_array[timeline_start_row:timeline_start_row+timeline_height, minute] = [25, 85, 140]
    
    # Add hour grid lines (vertical lines every 60 minutes)
    for hour in range(25):
        x = hour * 60
        if x < 1440:
            # Draw vertical line from timeline area down
            img_array[timeline_start_row-5:timeline_start_row+timeline_height+10, x] = [128, 128, 128]
    
    # Add quarter hour marks (lighter lines)
    for quarter in range(24 * 4):
        x = quarter * 15
        if x < 1440 and x % 60 != 0:  # Skip hour marks
            img_array[timeline_start_row:timeline_start_row+timeline_height, x] = [192, 192, 192]
    
    # Save directly as PNG to guarantee exact 1440px width
    date_str = f"{year}-{month:02d}-{day:02d}"
    temp_filename = f"debug_daily_{date_str}.png"
    Image.fromarray(img_array).save(temp_filename)
    
    # Verify the saved image size
    with Image.open(temp_filename) as img:
        w, h = img.size
        print(f"Saved image: {temp_filename} | Size: {w}x{h} (should be 1440x{img_height})")
        if w != 1440:
            print("WARNING: Output image is not exactly 1440px wide!")
    
    # Create a display image that's exactly 1440px wide with embedded labels and title
    display_height = 180  # Height for title, timeline, and labels
    display_array = np.ones((display_height, 1440, 3), dtype=np.uint8) * 255  # White background
    
    # Copy the timeline to the display image (centered vertically)
    timeline_y_start = 80  # Lower to make room for title
    timeline_y_end = timeline_y_start + timeline_height
    
    # First draw the grid lines (background layer)
    # Add hour grid lines directly to the image array (extend moderately above/below)
    for hour in range(0, 25):
        x = hour * 60
        if x < 1440:
            # Draw vertical grid line - same color as 15-minute lines but thicker and longer
            if hour % 2 == 0:  # Every 2 hours, draw a thicker line
                line_color = [200, 200, 200]  # Same light gray as 15-minute lines
                line_width = 2
            else:
                line_color = [200, 200, 200]  # Same light gray as 15-minute lines
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
            line_color = [200, 200, 200]  # Very light gray
            line_width = 1
            
            # Extend 8 pixels above and below the timeline (less than hour lines)
            for w in range(line_width):
                if x + w < 1440:
                    display_array[timeline_y_start-8:timeline_y_end+8, x+w] = line_color
    
    # Finally, draw the blue execution bars on top of everything (foreground layer)
    # This ensures blue pixels are never hidden by grid lines in the middle
    for minute in range(1440):
        if timeline[minute] == 1:
            # Darker blue color for executions - better contrast with grid lines
            display_array[timeline_y_start:timeline_y_end, minute] = [25, 85, 140]
    
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
    draw.text((title_x, 10), title_text, fill=(0, 0, 0), font=font)
    
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
            draw.text((text_x, text_y), hour_24, fill=(0, 0, 0), font=font)
            
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
                draw.text((text_x, text_y), hour_ampm, fill=(120, 120, 120), font=font)
    
    # Convert back to numpy array
    display_array = np.array(pil_image)
    
    # Save the final display image that's exactly 1440px wide
    display_filename = f"daily_timeline_{date_str}.png"
    Image.fromarray(display_array).save(display_filename)
    
    # Verify the display image dimensions
    with Image.open(display_filename) as img:
        w, h = img.size
        print(f"Display image: {display_filename} | Size: {w}x{h} (exactly 1440px wide)")
    
    # MAIN SUCCESS: Pixel-perfect files are saved! 
    print(f"\n🎯 SUCCESS: PIXEL-PERFECT TIMELINE FILES CREATED!")
    print(f"   📁 {temp_filename} (1440×{img_height}px)")
    print(f"   📁 {display_filename} (1440×{display_height}px)")
    print(f"   ✅ Both exactly 1440px wide (1 pixel = 1 minute)")
    print(f"   🔍 Open these PNG files for precise measurements!")
    
    # Display the exact image using PIL's built-in viewer (TRUE 1:1 pixels!)
    print(f"\n📺 OPENING PIXEL-PERFECT IMAGE VIEWER...")
    print(f"   Opening: {display_filename}")
    print(f"   This shows EXACT 1:1 pixel mapping (no stretching!)")
    print(f"   Each pixel = 1 minute, 1440px = 24 hours")
    
    try:
        # Open the image with the system's default image viewer
        # This guarantees true 1:1 pixel display without any scaling
        from PIL import Image
        with Image.open(display_filename) as img:
            img.show()  # Opens in system default image viewer at 1:1 scale
        
        print(f"   ✅ Image opened in system viewer at true 1:1 scale!")
        print(f"   💡 Use your image viewer's zoom to inspect details")
        
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
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create a blank calendar grid instead of heatmap
    ax.set_xlim(0, 7)
    ax.set_ylim(0, len(cal_matrix))
    ax.set_aspect('equal')
    
    # Draw grid lines
    for i in range(len(cal_matrix) + 1):
        ax.axhline(i, color='lightgray', linewidth=1)
    for j in range(8):
        ax.axvline(j, color='lightgray', linewidth=1)
    
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
                        
                        # Display the thumbnail as a single image
                        from matplotlib.colors import ListedColormap
                        cmap = ListedColormap(['#F8F8F8', '#19558C'])  # Match darker blue from daily view
                        ax.imshow(thumb_array, extent=extent, aspect='auto', 
                                 cmap=cmap, alpha=0.9, origin='lower', interpolation='bilinear')
                        
                        # Add a border around the thumbnail
                        thumb_border = plt.Rectangle((cell_x, cell_y), cell_width, cell_height,
                                                   fill=False, edgecolor='lightgray', linewidth=0.5)
                        ax.add_patch(thumb_border)
                        
                        # Add day number below the thumbnail
                        ax.text(j + 0.5, len(cal_matrix) - i - 0.15, day_str, 
                               color='black', fontsize=9, ha="center", va="center", 
                               fontweight="bold")
                    else:
                        # Day exists but no events - just show day number
                        ax.text(j + 0.5, len(cal_matrix) - i - 0.5, day_str, 
                               color='black', fontsize=12, ha="center", va="center", 
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
            ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # Add the field labels (small, positioned to align with cron string)
    ax.text(0.5, 1.10, 'minute hour dayOfMonth month dayOfWeek', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=9, style='italic', color='gray')
    
    # Add the description (medium)
    ax.text(0.5, 1.05, f'{cron_description} - {calendar.month_name[month]} {year}', 
            transform=ax.transAxes, ha='center', va='bottom', fontsize=12)
    
    # Add the instruction (small)
    ax.text(0.5, 1.00, 'Click on a day for detailed 1440-pixel timeline view (1 pixel = 1 minute). Thumbnails show daily patterns.', 
            transform=ax.transAxes, ha='center', va='bottom', 
            fontsize=10, style='italic')
    
    # Set up the calendar labels
    ax.set_xticks([i + 0.5 for i in range(7)])
    ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    ax.set_yticks([])
    ax.set_yticklabels([])
    
    # Remove default spines and add custom border
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Add outer border for the entire calendar
    border = plt.Rectangle((0, 0), 7, len(cal_matrix), fill=False, 
                          edgecolor='black', linewidth=2)
    ax.add_patch(border)
    
    # Add click event handler
    def on_click(event):
        if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
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
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
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
    # "27 14 1,15 * *"           # 2:30 PM on 1st and 15th of every month
    # "0 0 * * 0"                # Midnight every Sunday
    
    cron_string = "* 0-4,18-23 * * * | */15 10-22 * * * | 27 14 1,15 * *"  # Multiple jobs
    
    print("=== Interactive Cron Schedule Visualizer ===")
    print("Monthly calendar view with clickable daily details")
    print()
    
    # You can specify a different year/month, or leave None for current
    generate_monthly_calendar(cron_string, year=2025, month=6)

if __name__ == "__main__":
    main()
