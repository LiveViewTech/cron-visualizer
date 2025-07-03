#!/usr/bin/env python3
"""
Hello World - Main Python File
A simple hello world program for the cronScheduleVisualizer project.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
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

def main():
    """    
    Creates a 24x60 grid representing hours and minutes of a day, marks execution 
    times for an arbitrary cron pattern, and generates a heatmap visualization.
    """

    cron_string = "* 0-4,18-23 * * *"  # Edit this line to change the cron string

    print("Welcome to the Cron Schedule Visualizer!")
    print(f"Parsing cron string: {cron_string}")

    # Parse the cron string
    parts = cron_string.split()
    if len(parts) != 5:
        print("Error: Invalid cron string format. Expected 5 parts (minute hour day month weekday)")
        return

    # Parse each part of the cron string
    minutes = parse_cron_part(parts[0], 0, 59)
    hours = parse_cron_part(parts[1], 0, 23)
    
    print(f"Parsed minutes: {minutes[:10]}{'...' if len(minutes) > 10 else ''}")
    print(f"Parsed hours: {hours}")

    # Create a DataFrame to represent the 24x60 grid of a day
    df = pd.DataFrame(0, index=range(24), columns=range(60))

    # Mark the execution times in the DataFrame
    for hour in hours:
        for minute in minutes:
            df.loc[hour, minute] = 1

    print(f"Total execution times marked: {len(hours) * len(minutes)}")

    # Create the heatmap
    plt.figure(figsize=(16, 8))
    ax = sns.heatmap(df.T, cmap=["lightgrey", "#FF5733"], cbar=False, linewidths=.5, linecolor='white')

    # Customize the plot
    ax.set_title(f'Cron Job Execution Heatmap for "{cron_string}"', fontsize=16, pad=20)
    ax.set_xlabel('Hour of the Day', fontsize=12)
    ax.set_ylabel('Minute of the Hour', fontsize=12)

    # Set ticks to be more readable
    ax.set_xticks([i + 0.5 for i in range(24)])
    ax.set_xticklabels(range(24))
    # Set y-ticks to show the range clearly
    ax.set_yticks([i + 0.5 for i in range(0, 61, 5)])
    ax.set_yticklabels([f'{i:02}' for i in range(0, 61, 5)])

    # Invert y-axis to have 0 at the top
    ax.invert_yaxis()

    plt.tight_layout()
    
    # Find the next available file number
    counter = 1
    while os.path.exists(f"cron_heatmap_{counter}.png"):
        counter += 1
    
    filename = f"cron_heatmap_{counter}.png"
    plt.savefig(filename)
    plt.show()
    print(f"Your cron string is visually represented and saved as '{filename}'.")

if __name__ == "__main__":
    main()
