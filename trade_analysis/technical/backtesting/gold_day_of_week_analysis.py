#!/usr/bin/env python3
"""
Analyze day-of-week patterns for gold during bull runs.

For each day of the week (Mon, Tue, Wed, Thu, Fri), calculate:
- Average return on that day during bull runs
- Best days to buy (lowest average return = best entry)
- Best days to sell (highest average return = best exit)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def identify_bull_runs(close: pd.Series, min_duration_days: int = 60, min_return_pct: float = 20.0) -> pd.DataFrame:
    """
    Identify bull runs: sustained uptrends with minimum duration and return.
    
    Returns DataFrame with columns: start_date, end_date, duration_days, total_return_pct
    """
    bull_runs = []
    
    # Use 200-day MA to identify bull market (price above MA)
    ma200 = close.rolling(200).mean()
    price_above_ma = close > ma200
    
    # Find periods where price is above MA200 and trending up
    i = 200
    while i < len(close) - min_duration_days:
        if not price_above_ma.iloc[i]:
            i += 1
            continue
        
        # Start of potential bull run
        start_idx = i
        start_price = close.iloc[i]
        start_date = close.index[i]
        
        # Find end: price drops below MA200 or significant pullback
        end_idx = start_idx
        peak_price = start_price
        for j in range(start_idx + 1, len(close)):
            if close.iloc[j] > peak_price:
                peak_price = close.iloc[j]
            # End if: below MA200, or pullback > 15% from peak
            if not price_above_ma.iloc[j] or (peak_price - close.iloc[j]) / peak_price > 0.15:
                end_idx = j - 1
                break
            end_idx = j
        
        # Check if this qualifies as a bull run
        duration = (close.index[end_idx] - start_date).days
        total_return = (close.iloc[end_idx] / start_price - 1) * 100
        
        if duration >= min_duration_days and total_return >= min_return_pct:
            bull_runs.append({
                'start_date': start_date,
                'end_date': close.index[end_idx],
                'duration_days': duration,
                'total_return_pct': total_return,
                'start_price': start_price,
                'end_price': close.iloc[end_idx],
            })
            i = end_idx + 1
        else:
            i += 1
    
    return pd.DataFrame(bull_runs)


def analyze_day_of_week_returns(close: pd.Series, bull_runs_df: pd.DataFrame) -> dict:
    """
    For each day of week, calculate average return during bull runs.
    
    Returns dict with day -> {avg_return, count, buy_rank, sell_rank}
    """
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_returns = {day: [] for day in day_names}
    
    # For each bull run, get daily returns and group by day of week
    for _, run in bull_runs_df.iterrows():
        start = run['start_date']
        end = run['end_date']
        
        # Get data for this bull run
        run_data = close[(close.index >= start) & (close.index <= end)]
        if len(run_data) < 2:
            continue
        
        # Calculate daily returns
        daily_returns = run_data.pct_change().dropna() * 100
        
        # Group by day of week
        for date, ret in daily_returns.items():
            day_name = day_names[date.weekday()]
            day_returns[day_name].append(ret)
    
    # Calculate statistics
    results = {}
    for day in day_names:
        returns = day_returns[day]
        if len(returns) > 0:
            results[day] = {
                'avg_return': float(np.mean(returns)),
                'median_return': float(np.median(returns)),
                'count': len(returns),
                'std': float(np.std(returns)),
                'win_rate': (np.array(returns) > 0).sum() / len(returns) * 100,
            }
        else:
            results[day] = {
                'avg_return': 0.0,
                'median_return': 0.0,
                'count': 0,
                'std': 0.0,
                'win_rate': 0.0,
            }
    
    # Rank days: best to buy = lowest avg return, best to sell = highest avg return
    sorted_by_return = sorted(results.items(), key=lambda x: x[1]['avg_return'])
    for rank, (day, _) in enumerate(sorted_by_return, 1):
        results[day]['buy_rank'] = rank  # Lower return = better to buy
        results[day]['sell_rank'] = len(sorted_by_return) - rank + 1  # Higher return = better to sell
    
    return results


def main():
    print("=" * 70)
    print("Gold Day-of-Week Analysis (Bull Runs)")
    print("=" * 70)
    
    # Download gold data
    print("\nDownloading gold data (GC=F)...")
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period="max", interval="1d")
    
    if df is None or len(df) < 500:
        print("Error: Insufficient gold data")
        return
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    df.index = pd.to_datetime(df.index)
    
    close = df['close']
    print(f"  Data range: {close.index[0].date()} to {close.index[-1].date()}")
    print(f"  Total days: {len(close)}")
    
    # Identify bull runs
    print("\nIdentifying bull runs (price > MA200, min 60 days, min 20% return)...")
    bull_runs = identify_bull_runs(close, min_duration_days=60, min_return_pct=20.0)
    print(f"  Found {len(bull_runs)} bull runs")
    
    if len(bull_runs) == 0:
        print("  No bull runs found. Trying less strict criteria...")
        bull_runs = identify_bull_runs(close, min_duration_days=30, min_return_pct=15.0)
        print(f"  Found {len(bull_runs)} bull runs (relaxed criteria)")
    
    if len(bull_runs) > 0:
        print("\n  Bull runs:")
        for i, run in bull_runs.iterrows():
            print(f"    {run['start_date'].date()} to {run['end_date'].date()}: "
                  f"{run['duration_days']} days, {run['total_return_pct']:.1f}% return")
    
    # Analyze day-of-week returns
    print("\nAnalyzing day-of-week returns during bull runs...")
    day_results = analyze_day_of_week_returns(close, bull_runs)
    
    # Print results
    print("\n" + "=" * 70)
    print("DAY-OF-WEEK STATISTICS (Bull Runs)")
    print("=" * 70)
    print(f"{'Day':<12} {'Avg Return':<12} {'Median':<10} {'Count':<8} {'Win Rate':<10} {'Buy Rank':<10} {'Sell Rank':<10}")
    print("-" * 70)
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        r = day_results[day]
        print(f"{day:<12} {r['avg_return']:>+10.3f}%  {r['median_return']:>+8.3f}%  {r['count']:>6}  "
              f"{r['win_rate']:>7.1f}%  {r['buy_rank']:>8}  {r['sell_rank']:>8}")
    
    # Summary
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    # Best days to buy (lowest average return)
    sorted_buy = sorted(day_results.items(), key=lambda x: x[1]['avg_return'])
    best_buy = sorted_buy[0][0]
    print(f"\nBest day to BUY (lowest avg return): {best_buy} ({day_results[best_buy]['avg_return']:+.3f}%)")
    print(f"  Rationale: Lower average return = better entry price")
    
    # Best days to sell (highest average return)
    sorted_sell = sorted(day_results.items(), key=lambda x: x[1]['avg_return'], reverse=True)
    best_sell = sorted_sell[0][0]
    print(f"\nBest day to SELL (highest avg return): {best_sell} ({day_results[best_sell]['avg_return']:+.3f}%)")
    print(f"  Rationale: Higher average return = better exit price")
    
    print("\nNote: These are statistical averages during bull runs. Actual results may vary.")


if __name__ == "__main__":
    main()
