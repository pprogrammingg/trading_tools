#!/usr/bin/env python3
"""
Monitor analysis progress and show progress bar
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from pathlib import Path
from datetime import datetime
import json

def get_progress():
    """Get current analysis progress"""
    result_dir = Path("result_scores")
    result_files = list(result_dir.glob("*_results.json"))

    try:
        from config_loader import get_symbols_config
        config = get_symbols_config()
    except Exception:
        config = {}
    total_categories = len(config)
    completed_categories = len(result_files)
    
    # Get latest file modification time
    if result_files:
        latest = max(result_files, key=lambda p: p.stat().st_mtime)
        last_update = datetime.fromtimestamp(latest.stat().st_mtime)
        age = (datetime.now() - last_update).total_seconds()
    else:
        age = 999999
        last_update = None
    
    return {
        'completed': completed_categories,
        'total': total_categories,
        'progress_pct': (completed_categories / total_categories) * 100 if total_categories > 0 else 0,
        'last_update': last_update,
        'age_seconds': age,
        'is_active': age < 300  # Active if updated in last 5 minutes
    }

def print_progress_bar(progress_pct, width=50):
    """Print a progress bar"""
    filled = int(width * progress_pct / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {progress_pct:.1f}%"

def main():
    """Monitor and display progress"""
    print("\n" + "="*80)
    print("📊 ANALYSIS PROGRESS MONITOR")
    print("="*80 + "\n")
    
    prev_completed = 0
    
    while True:
        progress = get_progress()
        
        # Clear line and print progress
        print(f"\r{print_progress_bar(progress['progress_pct'])} | "
              f"Completed: {progress['completed']}/{progress['total']} categories", end='', flush=True)
        
        # Show status
        if progress['completed'] > prev_completed:
            print(f"\n✅ Category {progress['completed']} completed!")
            prev_completed = progress['completed']
        
        # Check if complete
        if progress['completed'] >= progress['total']:
            print("\n\n" + "="*80)
            print("✅ ANALYSIS COMPLETE!")
            print("="*80)
            break
        
        # Check if stalled
        if not progress['is_active'] and progress['completed'] < progress['total']:
            print(f"\n⚠️  No activity for {progress['age_seconds']/60:.1f} minutes")
            print("   Analysis may have stalled or completed")
            break
        
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
