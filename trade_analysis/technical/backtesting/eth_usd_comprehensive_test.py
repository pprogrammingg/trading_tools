#!/usr/bin/env python3
"""
ETH-USD Comprehensive Strategy Test
Tests all recommended strategies across all timeframes for ETH-USD
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

class ETHUSDStrategyTest:
    def __init__(self):
        """Initialize comprehensive strategy test"""
        self.timeframes = ["4H", "1D", "2D", "1W", "2W", "1M"]
        self.symbol = "ETH-USD"
        self.category = "cryptocurrencies"
        
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
    
    def test_strategy(self, timeframe, buy_threshold=5.5, sell_threshold=-2.0, 
                     stop_loss_pct=0.20, dca_amount=5.0, max_positions=10,
                     use_trailing_stop=False, trailing_stop_pct=0.15,
                     partial_profit_taking=False, profit_target_1=0.15, profit_target_2=0.30):
        """
        Test a specific strategy configuration
        
        Args:
            timeframe: Timeframe to test
            buy_threshold: Minimum score to buy
            sell_threshold: Maximum score to sell
            stop_loss_pct: Stop loss percentage
            dca_amount: DCA amount per buy
            max_positions: Maximum DCA positions
            use_trailing_stop: Use trailing stop loss
            trailing_stop_pct: Trailing stop percentage
            partial_profit_taking: Take partial profits
            profit_target_1: First profit target (sell 50%)
            profit_target_2: Second profit target (sell remaining)
        """
        print(f"  Testing {timeframe} (Buy: {buy_threshold}, Sell: {sell_threshold}, "
              f"Stop Loss: {stop_loss_pct*100:.0f}%)...", end=" ")
        
        # Initialize
        cash = 0.0
        positions = []
        trades = []
        total_invested = 0.0
        portfolio_history = []
        
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Download data - use longer periods for larger timeframes
            if timeframe == "4H":
                df_1h = ticker.history(period="60d", interval="1h")
                if len(df_1h) == 0:
                    print("✗ (no data)")
                    return None
                df = self.resample_to_timeframe(df_1h, timeframe)
            elif timeframe in ["2W", "1M"]:
                # Use longer history for monthly/weekly timeframes
                df = ticker.history(period="2y", interval="1d")
                if len(df) == 0:
                    print("✗ (no data)")
                    return None
                df = self.resample_to_timeframe(df, timeframe)
            else:
                df = ticker.history(period="1y", interval="1d")
                if len(df) == 0:
                    print("✗ (no data)")
                    return None
                df = self.resample_to_timeframe(df, timeframe)
            
            # Adjust minimum data requirement based on timeframe
            min_data_points = {
                "4H": 50,
                "1D": 50,
                "2D": 40,
                "1W": 30,
                "2W": 20,
                "1M": 15
            }
            
            required_points = min_data_points.get(timeframe, 50)
            if len(df) < required_points:
                print(f"✗ (insufficient data: {len(df)} < {required_points})")
                return None
            
            market_context = get_market_context()
            all_dates = sorted(df.index)
            
            # Track highest price for trailing stop
            position_highs = {}
            
            # Adjust minimum history based on timeframe
            min_history = {
                "4H": 50,
                "1D": 50,
                "2D": 40,
                "1W": 30,
                "2W": 20,
                "1M": 15
            }
            
            required_history = min_history.get(timeframe, 50)
            
            # Run simulation
            for i, current_date in enumerate(all_dates):
                if i < required_history:
                    continue
                
                df_historical = df[df.index <= current_date]
                if len(df_historical) < required_history:
                    continue
                
                current_price = df_historical['Close'].iloc[-1]
                
                # Check stop loss and trailing stops
                positions_to_remove = []
                for j, position in enumerate(positions):
                    entry_price = position['entry_price']
                    position_id = id(position)
                    
                    # Update highest price for trailing stop
                    if use_trailing_stop:
                        if position_id not in position_highs:
                            position_highs[position_id] = entry_price
                        if current_price > position_highs[position_id]:
                            position_highs[position_id] = current_price
                        
                        # Check trailing stop
                        trailing_stop_price = position_highs[position_id] * (1 - trailing_stop_pct)
                        if current_price <= trailing_stop_price:
                            return_pct = (current_price / entry_price - 1) * 100
                            proceeds = position['shares'] * current_price
                            cash += proceeds
                            
                            trades.append({
                                'type': 'SELL',
                                'timeframe': timeframe,
                                'entry_price': entry_price,
                                'exit_price': current_price,
                                'return_pct': return_pct,
                                'reason': 'trailing_stop',
                                'date': current_date
                            })
                            
                            positions_to_remove.append(j)
                            if position_id in position_highs:
                                del position_highs[position_id]
                            continue
                    
                    # Check regular stop loss
                    return_pct = (current_price / entry_price - 1) * 100
                    if return_pct <= -stop_loss_pct * 100:
                        proceeds = position['shares'] * current_price
                        cash += proceeds
                        
                        trades.append({
                            'type': 'SELL',
                            'timeframe': timeframe,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'return_pct': return_pct,
                            'reason': 'stop_loss',
                            'date': current_date
                        })
                        
                        positions_to_remove.append(j)
                        if position_id in position_highs:
                            del position_highs[position_id]
                        continue
                    
                    # Check partial profit taking
                    if partial_profit_taking:
                        if return_pct >= profit_target_1 * 100 and not position.get('partial_sold', False):
                            # Sell 50%
                            shares_to_sell = position['shares'] * 0.5
                            proceeds = shares_to_sell * current_price
                            cash += proceeds
                            
                            position['shares'] *= 0.5
                            position['partial_sold'] = True
                            
                            trades.append({
                                'type': 'SELL_PARTIAL',
                                'timeframe': timeframe,
                                'entry_price': entry_price,
                                'exit_price': current_price,
                                'return_pct': return_pct,
                                'shares': shares_to_sell,
                                'reason': f'partial_profit_{profit_target_1*100:.0f}%',
                                'date': current_date
                            })
                        
                        elif return_pct >= profit_target_2 * 100:
                            # Sell remaining
                            proceeds = position['shares'] * current_price
                            cash += proceeds
                            
                            trades.append({
                                'type': 'SELL',
                                'timeframe': timeframe,
                                'entry_price': entry_price,
                                'exit_price': current_price,
                                'return_pct': return_pct,
                                'reason': f'profit_target_{profit_target_2*100:.0f}%',
                                'date': current_date
                            })
                            
                            positions_to_remove.append(j)
                            if position_id in position_highs:
                                del position_highs[position_id]
                
                # Remove sold positions
                for j in reversed(positions_to_remove):
                    positions.pop(j)
                
                # Calculate score
                try:
                    score_result = improved_scoring(df_historical, self.category, 
                                                   timeframe=timeframe, market_context=market_context)
                    score = score_result.get('score', 0)
                except:
                    score = 0
                
                # Check sell signal
                if score <= sell_threshold and len(positions) > 0:
                    for position in positions:
                        return_pct = (current_price / position['entry_price'] - 1) * 100
                        proceeds = position['shares'] * current_price
                        cash += proceeds
                        
                        trades.append({
                            'type': 'SELL',
                            'timeframe': timeframe,
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'return_pct': return_pct,
                            'reason': 'sell_signal',
                            'date': current_date
                        })
                    
                    positions = []
                    position_highs = {}
                
                # Check buy signal
                if score >= buy_threshold and len(positions) < max_positions:
                    if cash < dca_amount:
                        cash += dca_amount
                        total_invested += dca_amount
                    
                    shares = dca_amount / current_price
                    cost = shares * current_price
                    
                    if cost <= cash:
                        cash -= cost
                        
                        position = {
                            'shares': shares,
                            'entry_price': current_price,
                            'entry_date': current_date,
                            'entry_score': score
                        }
                        positions.append(position)
                        
                        trades.append({
                            'type': 'BUY',
                            'timeframe': timeframe,
                            'price': current_price,
                            'shares': shares,
                            'score': score,
                            'date': current_date
                        })
                
                # Record portfolio value
                portfolio_value = cash + sum(p['shares'] * current_price for p in positions)
                portfolio_history.append((current_date, portfolio_value))
            
            # Close all positions
            if len(positions) > 0 and len(df) > 0:
                final_price = df['Close'].iloc[-1]
                for position in positions:
                    return_pct = (final_price / position['entry_price'] - 1) * 100
                    proceeds = position['shares'] * final_price
                    cash += proceeds
                    
                    trades.append({
                        'type': 'SELL',
                        'timeframe': timeframe,
                        'entry_price': position['entry_price'],
                        'exit_price': final_price,
                        'return_pct': return_pct,
                        'reason': 'end_of_simulation',
                        'date': all_dates[-1]
                    })
            
            # Calculate metrics
            final_value = cash
            total_return = ((final_value / total_invested - 1) * 100) if total_invested > 0 else 0
            
            buy_trades = [t for t in trades if t['type'] == 'BUY']
            sell_trades = [t for t in trades if t['type'] in ['SELL', 'SELL_PARTIAL']]
            winning_trades = [t for t in sell_trades if t.get('return_pct', 0) > 0]
            losing_trades = [t for t in sell_trades if t.get('return_pct', 0) <= 0]
            
            win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
            avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
            
            # Calculate max drawdown
            if portfolio_history:
                values = [v for _, v in portfolio_history]
                if values and total_invested > 0:
                    peak = values[0]
                    max_dd = 0
                    for v in values:
                        if v > peak:
                            peak = v
                        dd = ((v - peak) / peak) * 100 if peak > 0 else 0
                        if dd < max_dd:
                            max_dd = dd
                else:
                    max_dd = 0
            else:
                max_dd = 0
            
            result = {
                'timeframe': timeframe,
                'strategy': {
                    'buy_threshold': buy_threshold,
                    'sell_threshold': sell_threshold,
                    'stop_loss_pct': stop_loss_pct,
                    'trailing_stop': use_trailing_stop,
                    'partial_profit': partial_profit_taking
                },
                'total_invested': total_invested,
                'final_value': final_value,
                'total_return_pct': total_return,
                'max_drawdown_pct': max_dd,
                'total_trades': len(trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_win_pct': avg_win,
                'avg_loss_pct': avg_loss,
                'trades': trades
            }
            
            print(f"✓ (Return: {total_return:+.2f}%, Win Rate: {win_rate:.1f}%, "
                  f"Max DD: {max_dd:.2f}%)")
            return result
            
        except Exception as e:
            print(f"✗ (error: {e})")
            return None
    
    def run_comprehensive_test(self):
        """Run comprehensive test with all recommended strategies"""
        print("\n" + "="*80)
        print("ETH-USD COMPREHENSIVE STRATEGY TEST")
        print("Testing all recommended strategies across all timeframes")
        print("="*80 + "\n")
        
        results = {}
        
        # Strategy 1: Basic DCA + Stop Loss (Recommended)
        print("Strategy 1: Basic DCA + Stop Loss (Recommended)")
        print("-" * 80)
        for tf in self.timeframes:
            result = self.test_strategy(
                timeframe=tf,
                buy_threshold=5.5,
                sell_threshold=-2.0,
                stop_loss_pct=0.20,
                dca_amount=5.0,
                max_positions=10
            )
            if result:
                key = f"{tf}_basic"
                results[key] = result
        
        # Strategy 2: DCA + Trailing Stop
        print("\nStrategy 2: DCA + Trailing Stop (15%)")
        print("-" * 80)
        for tf in self.timeframes:
            result = self.test_strategy(
                timeframe=tf,
                buy_threshold=5.5,
                sell_threshold=-2.0,
                stop_loss_pct=0.20,
                dca_amount=5.0,
                max_positions=10,
                use_trailing_stop=True,
                trailing_stop_pct=0.15
            )
            if result:
                key = f"{tf}_trailing"
                results[key] = result
        
        # Strategy 3: DCA + Partial Profit Taking
        print("\nStrategy 3: DCA + Partial Profit Taking (15% / 30%)")
        print("-" * 80)
        for tf in self.timeframes:
            result = self.test_strategy(
                timeframe=tf,
                buy_threshold=5.5,
                sell_threshold=-2.0,
                stop_loss_pct=0.20,
                dca_amount=5.0,
                max_positions=10,
                partial_profit_taking=True,
                profit_target_1=0.15,
                profit_target_2=0.30
            )
            if result:
                key = f"{tf}_partial"
                results[key] = result
        
        # Strategy 4: DCA + Trailing Stop + Partial Profit
        print("\nStrategy 4: DCA + Trailing Stop + Partial Profit (Best of Both)")
        print("-" * 80)
        for tf in self.timeframes:
            result = self.test_strategy(
                timeframe=tf,
                buy_threshold=5.5,
                sell_threshold=-2.0,
                stop_loss_pct=0.20,
                dca_amount=5.0,
                max_positions=10,
                use_trailing_stop=True,
                trailing_stop_pct=0.15,
                partial_profit_taking=True,
                profit_target_1=0.15,
                profit_target_2=0.30
            )
            if result:
                key = f"{tf}_combined"
                results[key] = result
        
        return results

def main():
    """Run comprehensive ETH-USD test"""
    tester = ETHUSDStrategyTest()
    results = tester.run_comprehensive_test()
    
    # Analyze results
    print("\n" + "="*80)
    print("RESULTS ANALYSIS")
    print("="*80 + "\n")
    
    # Group by timeframe
    timeframe_results = defaultdict(list)
    for key, result in results.items():
        tf = result['timeframe']
        timeframe_results[tf].append(result)
    
    # Find best strategy for each timeframe
    print("Best Strategy by Timeframe:")
    print("-" * 80)
    print(f"{'Timeframe':<10} {'Strategy':<20} {'Return':<12} {'Win Rate':<12} {'Max DD':<12}")
    print("-" * 80)
    
    best_overall = None
    best_return = float('-inf')
    
    for tf in tester.timeframes:
        if tf in timeframe_results:
            tf_results = timeframe_results[tf]
            best_strategy = max(tf_results, key=lambda x: x['total_return_pct'])
            
            strategy_name = "Basic" if "basic" in [k for k in results.keys() if tf in k][0] else \
                           "Trailing" if "trailing" in [k for k in results.keys() if tf in k][0] else \
                           "Partial" if "partial" in [k for k in results.keys() if tf in k][0] else \
                           "Combined"
            
            print(f"{tf:<10} {strategy_name:<20} {best_strategy['total_return_pct']:>11.2f}% "
                  f"{best_strategy['win_rate']:>11.1f}% {best_strategy['max_drawdown_pct']:>11.2f}%")
            
            if best_strategy['total_return_pct'] > best_return:
                best_return = best_strategy['total_return_pct']
                best_overall = best_strategy
    
    # Overall best
    print("\n" + "="*80)
    print("OVERALL BEST STRATEGY:")
    print("="*80)
    if best_overall:
        print(f"Timeframe: {best_overall['timeframe']}")
        print(f"Return: {best_overall['total_return_pct']:+.2f}%")
        print(f"Win Rate: {best_overall['win_rate']:.1f}%")
        print(f"Max Drawdown: {best_overall['max_drawdown_pct']:.2f}%")
        print(f"Total Invested: ${best_overall['total_invested']:.2f}")
        print(f"Final Value: ${best_overall['final_value']:.2f}")
        print(f"Total Trades: {best_overall['total_trades']}")
        print(f"Winning Trades: {best_overall['winning_trades']}")
        print(f"Losing Trades: {best_overall['losing_trades']}")
        print(f"Avg Win: {best_overall['avg_win_pct']:+.2f}%")
        print(f"Avg Loss: {best_overall['avg_loss_pct']:+.2f}%")
    
    # Save results
    output_file = 'eth_usd_comprehensive_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'results': results,
            'best_overall': best_overall
        }, f, indent=2, default=str)
    
    print(f"\n✓ Full results saved to {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
