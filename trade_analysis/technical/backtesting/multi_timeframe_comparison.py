#!/usr/bin/env python3
"""
Multi-Timeframe Comparison Experiment
Tests SOL, ETH, and QBTS across all timeframes (4H, 1D, 2D, 1W, 2W, 1M)
to identify best-performing timeframe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from scoring.improved_scoring import improved_scoring
from indicators.market_context import get_market_context

class MultiTimeframeSimulation:
    def __init__(self, dca_amount=5.0, buy_threshold=5.5, sell_threshold=-2.0, 
                 stop_loss_pct=0.20, max_positions_per_symbol=10):
        """
        Initialize multi-timeframe simulation
        
        Args:
            dca_amount: Amount to invest per buy signal ($5)
            buy_threshold: Minimum score to buy
            sell_threshold: Maximum score to sell
            stop_loss_pct: Stop loss percentage (20%)
            max_positions_per_symbol: Maximum DCA positions per symbol
        """
        self.dca_amount = dca_amount
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss_pct = stop_loss_pct
        self.max_positions_per_symbol = max_positions_per_symbol
        
        # Timeframes to test
        self.timeframes = ["4H", "1D", "2D", "1W", "2W", "1M"]
        
    def resample_to_timeframe(self, df, timeframe):
        """Resample data to specified timeframe"""
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        if timeframe == "4H":
            df_resampled = df.resample('4h').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == "1D":
            df_resampled = df.resample('D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == "2D":
            df_resampled = df.resample('2D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == "1W":
            df_resampled = df.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == "2W":
            df_resampled = df.resample('2W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == "1M":
            df_resampled = df.resample('ME').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        else:
            df_resampled = df
        
        df_resampled.columns = [col.capitalize() for col in df_resampled.columns]
        return df_resampled
    
    def check_stop_loss(self, position, current_price):
        """Check if stop loss should trigger"""
        entry_price = position['entry_price']
        return_pct = (current_price / entry_price - 1) * 100
        return return_pct <= -self.stop_loss_pct * 100, return_pct
    
    def run_timeframe_simulation(self, symbol, timeframe, category="cryptocurrencies"):
        """Run simulation for a single symbol and timeframe"""
        print(f"  Testing {symbol} on {timeframe}...", end=" ")
        
        # Initialize for this timeframe
        cash = 0.0
        positions = []
        trades = []
        total_invested = 0.0
        portfolio_history = []
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Download appropriate data
            if timeframe == "4H":
                df_1h = ticker.history(period="60d", interval="1h")
                if len(df_1h) == 0:
                    print("✗ (no data)")
                    return None
                df = self.resample_to_timeframe(df_1h, timeframe)
            else:
                df = ticker.history(period="1y", interval="1d")
                if len(df) == 0:
                    print("✗ (no data)")
                    return None
                df = self.resample_to_timeframe(df, timeframe)
            
            if len(df) < 50:
                print("✗ (insufficient data)")
                return None
            
            # Get market context
            market_context = get_market_context()
            
            # Get all dates
            all_dates = sorted(df.index)
            
            # Run simulation
            for i, current_date in enumerate(all_dates):
                if i < 50:  # Need history for indicators
                    continue
                
                # Get historical data up to current date
                df_historical = df[df.index <= current_date]
                if len(df_historical) < 50:
                    continue
                
                current_price = df_historical['Close'].iloc[-1]
                
                # Check stop loss for existing positions
                positions_to_remove = []
                for j, position in enumerate(positions):
                    should_sell, return_pct = self.check_stop_loss(position, current_price)
                    if should_sell:
                        # Sell position
                        proceeds = position['shares'] * current_price
                        cash += proceeds
                        
                        trades.append({
                            'type': 'SELL',
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'return_pct': return_pct,
                            'reason': 'stop_loss',
                            'date': current_date
                        })
                        
                        positions_to_remove.append(j)
                
                # Remove sold positions (in reverse order)
                for j in reversed(positions_to_remove):
                    positions.pop(j)
                
                # Calculate score
                try:
                    score_result = improved_scoring(df_historical, category, timeframe=timeframe, market_context=market_context)
                    score = score_result.get('score', 0)
                except:
                    score = 0
                
                # Check sell signal
                if score <= self.sell_threshold and len(positions) > 0:
                    # Sell all positions
                    for position in positions:
                        return_pct = (current_price / position['entry_price'] - 1) * 100
                        proceeds = position['shares'] * current_price
                        cash += proceeds
                        
                        trades.append({
                            'type': 'SELL',
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'return_pct': return_pct,
                            'reason': 'sell_signal',
                            'date': current_date
                        })
                    
                    positions = []
                
                # Check buy signal
                if score >= self.buy_threshold and len(positions) < self.max_positions_per_symbol:
                    # Need $5 to buy
                    if cash < self.dca_amount:
                        cash += self.dca_amount
                        total_invested += self.dca_amount
                    
                    # Calculate shares
                    shares = self.dca_amount / current_price
                    cost = shares * current_price
                    
                    if cost <= cash:
                        cash -= cost
                        
                        positions.append({
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date,
                            'entry_score': score
                        })
                        
                        trades.append({
                            'type': 'BUY',
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'price': current_price,
                            'shares': shares,
                            'score': score,
                            'date': current_date
                        })
                
                # Record portfolio value
                portfolio_value = cash + sum(p['shares'] * current_price for p in positions)
                portfolio_history.append((current_date, portfolio_value))
            
            # Close all positions at end
            if len(positions) > 0 and len(df) > 0:
                final_price = df['Close'].iloc[-1]
                for position in positions:
                    return_pct = (final_price / position['entry_price'] - 1) * 100
                    proceeds = position['shares'] * final_price
                    cash += proceeds
                    
                    trades.append({
                        'type': 'SELL',
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'entry_price': position['entry_price'],
                        'exit_price': final_price,
                        'return_pct': return_pct,
                        'reason': 'end_of_simulation',
                        'date': all_dates[-1]
                    })
            
            # Calculate final metrics
            final_value = cash
            total_return = ((final_value / total_invested - 1) * 100) if total_invested > 0 else 0
            
            buy_trades = [t for t in trades if t['type'] == 'BUY']
            sell_trades = [t for t in trades if t['type'] == 'SELL']
            winning_trades = [t for t in sell_trades if t.get('return_pct', 0) > 0]
            losing_trades = [t for t in sell_trades if t.get('return_pct', 0) <= 0]
            
            win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
            avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
            
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'total_invested': total_invested,
                'final_value': final_value,
                'total_return_pct': total_return,
                'total_trades': len(trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_win_pct': avg_win,
                'avg_loss_pct': avg_loss,
                'trades': trades,
                'portfolio_history': [(d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d), v) for d, v in portfolio_history]
            }
            
            print(f"✓ (Return: {total_return:+.2f}%, Win Rate: {win_rate:.1f}%)")
            return result
            
        except Exception as e:
            print(f"✗ (error: {e})")
            return None
    
    def run_experiment(self, symbols):
        """Run experiment across all symbols and timeframes"""
        print("\n" + "="*80)
        print("MULTI-TIMEFRAME COMPARISON EXPERIMENT")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Timeframes: {', '.join(self.timeframes)}")
        print(f"Strategy: DCA + Stop Loss (Buy: {self.buy_threshold}, Sell: {self.sell_threshold}, Stop Loss: {self.stop_loss_pct*100:.0f}%)")
        print("="*80 + "\n")
        
        results = {}
        
        # Determine category
        category_map = {
            'SOL-USD': 'cryptocurrencies',
            'ETH-USD': 'cryptocurrencies',
            'BTC-USD': 'cryptocurrencies',
            'QBTS': 'quantum'
        }
        
        for symbol in symbols:
            print(f"\nTesting {symbol}:")
            category = category_map.get(symbol, 'cryptocurrencies')
            results[symbol] = {}
            
            for timeframe in self.timeframes:
                result = self.run_timeframe_simulation(symbol, timeframe, category)
                if result:
                    results[symbol][timeframe] = result
        
        return results

def main():
    """Run multi-timeframe comparison experiment"""
    # Test symbols: SOL, ETH, QBTS
    symbols = ['SOL-USD', 'ETH-USD', 'QBTS']
    
    # Create simulation
    sim = MultiTimeframeSimulation(
        dca_amount=5.0,
        buy_threshold=5.5,
        sell_threshold=-2.0,
        stop_loss_pct=0.20,
        max_positions_per_symbol=10
    )
    
    # Run experiment
    results = sim.run_experiment(symbols)
    
    # Analyze and print results
    print("\n" + "="*80)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*80 + "\n")
    
    # Summary by timeframe
    timeframe_summary = defaultdict(lambda: {'total_invested': 0, 'final_value': 0, 'total_return': 0, 'win_rate': 0, 'count': 0})
    
    for symbol, symbol_results in results.items():
        print(f"\n{symbol} Performance by Timeframe:")
        print(f"{'Timeframe':<10} {'Invested':<12} {'Final Value':<12} {'Return':<10} {'Win Rate':<10} {'Trades':<8}")
        print("-" * 70)
        
        for timeframe in sim.timeframes:
            if timeframe in symbol_results:
                r = symbol_results[timeframe]
                print(f"{timeframe:<10} ${r['total_invested']:>10.2f} ${r['final_value']:>10.2f} "
                      f"{r['total_return_pct']:>9.2f}% {r['win_rate']:>9.1f}% {r['total_trades']:>7d}")
                
                # Aggregate for timeframe summary
                tf_sum = timeframe_summary[timeframe]
                tf_sum['total_invested'] += r['total_invested']
                tf_sum['final_value'] += r['final_value']
                tf_sum['win_rate'] += r['win_rate']
                tf_sum['count'] += 1
        
        # Find best timeframe for this symbol
        best_tf = None
        best_return = float('-inf')
        for timeframe in sim.timeframes:
            if timeframe in symbol_results:
                if symbol_results[timeframe]['total_return_pct'] > best_return:
                    best_return = symbol_results[timeframe]['total_return_pct']
                    best_tf = timeframe
        
        if best_tf:
            print(f"\n  ✅ Best Timeframe: {best_tf} ({best_return:+.2f}% return)")
    
    # Overall timeframe comparison
    print("\n" + "="*80)
    print("OVERALL TIMEFRAME PERFORMANCE (All Symbols Combined)")
    print("="*80)
    print(f"{'Timeframe':<10} {'Total Invested':<15} {'Final Value':<15} {'Avg Return':<12} {'Avg Win Rate':<12}")
    print("-" * 70)
    
    timeframe_rankings = []
    for timeframe in sim.timeframes:
        tf_sum = timeframe_summary[timeframe]
        if tf_sum['count'] > 0:
            avg_invested = tf_sum['total_invested'] / tf_sum['count']
            avg_final = tf_sum['final_value'] / tf_sum['count']
            avg_return = ((tf_sum['final_value'] / tf_sum['total_invested'] - 1) * 100) if tf_sum['total_invested'] > 0 else 0
            avg_win_rate = tf_sum['win_rate'] / tf_sum['count']
            
            timeframe_rankings.append({
                'timeframe': timeframe,
                'avg_return': avg_return,
                'avg_win_rate': avg_win_rate,
                'total_invested': tf_sum['total_invested'],
                'final_value': tf_sum['final_value']
            })
            
            print(f"{timeframe:<10} ${avg_invested:>13.2f} ${avg_final:>13.2f} "
                  f"{avg_return:>11.2f}% {avg_win_rate:>11.1f}%")
    
    # Rank timeframes
    timeframe_rankings.sort(key=lambda x: x['avg_return'], reverse=True)
    
    print("\n" + "="*80)
    print("TIMEFRAME RANKINGS (by Average Return)")
    print("="*80)
    for i, tf_data in enumerate(timeframe_rankings, 1):
        print(f"{i}. {tf_data['timeframe']:<6} - {tf_data['avg_return']:+.2f}% return, "
              f"{tf_data['avg_win_rate']:.1f}% win rate")
    
    # Save results
    output_file = 'multi_timeframe_comparison_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'results': results,
            'timeframe_summary': dict(timeframe_summary),
            'timeframe_rankings': timeframe_rankings
        }, f, indent=2, default=str)
    
    print(f"\n✓ Full results saved to {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
