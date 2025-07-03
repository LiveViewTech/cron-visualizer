#!/usr/bin/env python3
"""
Test script to debug calendar visualization
"""
from main import generate_monthly_calendar

# Test with a simpler cron that should clearly show all days
simple_cron = "0 12 * * *"  # Noon every day
print("Testing with simple cron: 0 12 * * * (noon every day)")
generate_monthly_calendar(simple_cron, year=2025, month=6)
