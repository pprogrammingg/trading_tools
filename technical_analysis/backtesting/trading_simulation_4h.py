#!/usr/bin/env python3
"""
Trading Simulation: $5 Investment with 4-Hour Analysis
Simulates trading decisions using 4H timeframe scoring on volatile assets
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
from technical_analysis import load_symbols_config

class TradingSimulation:
    def __init__(self, initial_capital=5.0, buy_threshold=6.0, sell_threshold=-2.0, 
                 stop_loss_pct=0.15, take_profit_pct=0.30, max_position_pct=1.0):
        """
        Initialize trading simulation
        
        Args:
            initial_capital: Starting capital in dollars
            buy_threshold: Minimum score to buy
            sell_threshold: Maximum score to sell (negative = sell signal)
            stop_loss_pct: Stop loss percentage (15% = sell if down 15%)
            take_profit_pct: Take profit percentage (30% = sell if up 30%)
            max_position_pct: Maximum percentage of capital per position (1.0 = 100%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {symbol: {'shares': float, 'entry_price': float, 'entry_date': datetime, 'entry_score': float}}
        self.trades = []  # List of all trades
        self.portfolio_value_history = []  # [(date, portfolio_value)]
        
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_pct = max_position_pct
        
    def get_portfolio_value(self, current_prices):
        """Calculate total portfolio value"""
        total_value = self.cash
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = position['shares'] * current_price
                total_value += position_value
        return total_value
    
    def check_stop_loss_take_profit(self, symbol, current_price, current_date):
        """Check if stop loss or take profit should trigger"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        
        # Calculate return
        return_pct = (current_price / entry_price - 1) * 100
        
        # Check stop loss
        if return_pct <= -self.stop_loss_pct * 100:
            return True, 'stop_loss', return_pct
        
        # Check take profit
        if return_pct >= self.take_profit_pct * 100:
            return True, 'take_profit', return_pct
        
        return False, None, return_pct
    
    def sell_position(self, symbol, current_price, current_date, reason='signal', return_pct=None):
        """Sell a position"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        shares = position['shares']
        entry_price = position['entry_price']
        entry_date = position['entry_date']
        entry_score = position['entry_score']
        
        # Calculate proceeds
        proceeds = shares * current_price
        self.cash += proceeds
        
        # Calculate return
        if return_pct is None:
            return_pct = (current_price / entry_price - 1) * 100
        
        # Record trade
        trade = {
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'exit_price': current_price,
            'entry_date': entry_date,
            'exit_date': current_date,
            'entry_score': entry_score,
            'return_pct': return_pct,
            'proceeds': proceeds,
            'reason': reason
        }
        self.trades.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        return True
    
    def buy_position(self, symbol, current_price, current_date, score):
        """Buy a position"""
        # Calculate position size (use max_position_pct of current portfolio value)
        portfolio_value = self.get_portfolio_value({symbol: current_price})
        max_investment = portfolio_value * self.max_position_pct
        
        # Don't buy if we don't have enough cash
        if self.cash < max_investment:
            max_investment = self.cash
        
        if max_investment < 0.01:  # Minimum $0.01
            return False
        
        # Calculate shares (account for fractional shares)
        shares = max_investment / current_price
        
        # Execute buy
        cost = shares * current_price
        if cost > self.cash:
            return False
        
        self.cash -= cost
        
        # Record position
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': current_price,
            'entry_date': current_date,
            'entry_score': score
        }
        
        # Record trade
        trade = {
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': current_price,
            'date': current_date,
            'score': score,
            'cost': cost
        }
        self.trades.append(trade)
        
        return True
    
    def run_simulation(self, symbols, category, start_date=None, end_date=None):
        """Run trading simulation on symbols"""
        print(f"\n{'='*80}")
        print(f"TRADING SIMULATION: ${self.initial_capital:.2f} Starting Capital")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Buy Threshold: {self.buy_threshold}, Sell Threshold: {self.sell_threshold}")
        print(f"Stop Loss: {self.stop_loss_pct*100:.0f}%, Take Profit: {self.take_profit_pct*100:.0f}%")
        print(f"{'='*80}\n")
        
        # Download data for all symbols
        symbol_data = {}
        for symbol in symbols:
            print(f"Downloading 4H data for {symbol}...", end=" ")
            try:
                # Try to download 1h data for last 60 days, then resample to 4h
                ticker = yf.Ticker(symbol)
                df_1h = ticker.history(period="60d", interval="1h")
                
                if len(df_1h) == 0:
                    # Fallback: use daily data and simulate 4H bars
                    print("(using daily data fallback)", end=" ")
                    df_daily = ticker.history(period="1y", interval="1d")
                    if len(df_daily) == 0:
                        print("✗ (no data)")
                        continue
                    # Create synthetic 4H bars from daily (6 bars per day)
                    df_4h = df_daily.resample('4h').ffill()
                    # Filter to only trading hours (rough approximation)
                    df_4h = df_4h[df_4h.index.hour.isin([0, 4, 8, 12, 16, 20])]
                else:
                    # Resample to 4H
                    df_4h = df_1h.resample('4h').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                
                if len(df_4h) < 50:
                    print(f"✗ (insufficient data: {len(df_4h)} bars)")
                    continue
                
                symbol_data[symbol] = df_4h
                print(f"✓ ({len(df_4h)} 4H bars)")
            except Exception as e:
                print(f"✗ (error: {e})")
                continue
        
        if len(symbol_data) == 0:
            print("No data available for any symbols!")
            return None
        
        # Get common date range
        all_dates = set()
        for df in symbol_data.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)
        
        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]
        
        print(f"\nSimulating from {all_dates[0]} to {all_dates[-1]} ({len(all_dates)} periods)\n")
        
        # Get market context (use current for all periods for simplicity)
        market_context = get_market_context()
        
        # Run simulation
        for i, current_date in enumerate(all_dates):
            if i < 50:  # Need enough history for indicators
                continue
            
            current_prices = {}
            scores = {}
            
            # Calculate scores for all symbols
            for symbol, df in symbol_data.items():
                # Get data up to current date
                df_historical = df[df.index <= current_date]
                
                if len(df_historical) < 50:
                    continue
                
                current_price = df_historical['Close'].iloc[-1]
                current_prices[symbol] = current_price
                
                try:
                    # Calculate score
                    score_result = improved_scoring(df_historical, category, timeframe="4H", market_context=market_context)
                    score = score_result.get('score', 0)
                    scores[symbol] = score
                except:
                    scores[symbol] = 0
            
            # Check stop loss / take profit for existing positions
            for symbol in list(self.positions.keys()):
                if symbol in current_prices:
                    should_sell, reason, return_pct = self.check_stop_loss_take_profit(
                        symbol, current_prices[symbol], current_date
                    )
                    if should_sell:
                        self.sell_position(symbol, current_prices[symbol], current_date, reason, return_pct)
            
            # Check sell signals (negative scores)
            for symbol in list(self.positions.keys()):
                if symbol in scores and scores[symbol] <= self.sell_threshold:
                    if symbol in current_prices:
                        self.sell_position(symbol, current_prices[symbol], current_date, 'sell_signal')
            
            # Check buy signals (high scores)
            for symbol in scores:
                if symbol not in self.positions and scores[symbol] >= self.buy_threshold:
                    if symbol in current_prices:
                        self.buy_position(symbol, current_prices[symbol], current_date, scores[symbol])
            
            # Record portfolio value
            portfolio_value = self.get_portfolio_value(current_prices)
            self.portfolio_value_history.append((current_date, portfolio_value))
        
        # Close all positions at end
        final_prices = {}
        for symbol, df in symbol_data.items():
            if len(df) > 0:
                final_prices[symbol] = df['Close'].iloc[-1]
        
        for symbol in list(self.positions.keys()):
            if symbol in final_prices:
                self.sell_position(symbol, final_prices[symbol], all_dates[-1], 'end_of_simulation')
        
        return self.generate_report(all_dates)
    
    def generate_report(self, all_dates):
        """Generate trading report"""
        # Calculate final portfolio value
        final_value = self.cash  # All positions closed
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # Calculate returns at different intervals
        interval_returns = {}
        intervals = {
            '30_days': 30,
            '60_days': 60,
            '90_days': 90,
            '6_months': 180,
            '1_year': 365
        }
        
        start_date = all_dates[0] if all_dates else datetime.now()
        
        for interval_name, days in intervals.items():
            target_date = start_date + timedelta(days=days)
            
            # Find closest portfolio value
            closest_value = self.initial_capital
            closest_date = start_date
            
            for date, value in self.portfolio_value_history:
                if date <= target_date and date > closest_date:
                    closest_value = value
                    closest_date = date
            
            if closest_date > start_date:
                interval_return = (closest_value / self.initial_capital - 1) * 100
                interval_returns[interval_name] = {
                    'date': closest_date,
                    'value': closest_value,
                    'return_pct': interval_return
                }
        
        # Final return
        interval_returns['final'] = {
            'date': all_dates[-1] if all_dates else datetime.now(),
            'value': final_value,
            'return_pct': total_return
        }
        
        # Trade statistics
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('return_pct', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('return_pct', 0) <= 0]
        
        avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
        
        report = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'interval_returns': interval_returns,
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'trades': self.trades,
            'portfolio_history': [(d.strftime('%Y-%m-%d %H:%M') if hasattr(d, 'strftime') else str(d), v) for d, v in self.portfolio_value_history]
        }
        
        return report

def main():
    """Run trading simulation"""
    # Select volatile assets (Quantum and Crypto)
    symbols_config = load_symbols_config()
    
    # Quantum stocks
    quantum_symbols = symbols_config.get('quantum', [])[:3]  # Top 3 quantum stocks
    
    # Crypto
    crypto_symbols = symbols_config.get('cryptocurrencies', [])[:2]  # Top 2 crypto
    
    # Combine
    test_symbols = quantum_symbols + crypto_symbols
    
    if len(test_symbols) == 0:
        print("No symbols found! Check symbols_config.json")
        return
    
    print(f"Selected symbols: {test_symbols}")
    
    # Determine category (use first symbol's category)
    category = 'quantum' if quantum_symbols else 'cryptocurrencies'
    
    # Create simulation
    sim = TradingSimulation(
        initial_capital=5.0,
        buy_threshold=6.0,  # Buy when score >= 6
        sell_threshold=-2.0,  # Sell when score <= -2
        stop_loss_pct=0.15,  # 15% stop loss
        take_profit_pct=0.30,  # 30% take profit
        max_position_pct=1.0  # Can use 100% of capital per position
    )
    
    # Run simulation
    report = sim.run_simulation(test_symbols, category)
    
    if report is None:
        print("Simulation failed!")
        return
    
    # Print report
    print("\n" + "="*80)
    print("TRADING SIMULATION RESULTS")
    print("="*80 + "\n")
    
    print(f"Initial Capital: ${report['initial_capital']:.2f}")
    print(f"Final Value: ${report['final_value']:.2f}")
    print(f"Total Return: {report['total_return_pct']:+.2f}%\n")
    
    print("Returns at Intervals:")
    for interval_name, data in report['interval_returns'].items():
        if interval_name != 'final':
            date_str = data['date'].strftime('%Y-%m-%d') if hasattr(data['date'], 'strftime') else str(data['date'])
            print(f"  {interval_name.replace('_', ' ').title():15s}: ${data['value']:.2f} ({data['return_pct']:+.2f}%) at {date_str}")
    
    final_data = report['interval_returns']['final']
    final_date_str = final_data['date'].strftime('%Y-%m-%d') if hasattr(final_data['date'], 'strftime') else str(final_data['date'])
    print(f"  Final:            : ${final_data['value']:.2f} ({final_data['return_pct']:+.2f}%) at {final_date_str}\n")
    
    print("Trade Statistics:")
    print(f"  Total Trades: {report['total_trades']}")
    print(f"  Buy Trades: {report['buy_trades']}")
    print(f"  Sell Trades: {report['sell_trades']}")
    print(f"  Winning Trades: {report['winning_trades']}")
    print(f"  Losing Trades: {report['losing_trades']}")
    print(f"  Win Rate: {report['win_rate']:.1f}%")
    print(f"  Avg Win: {report['avg_win_pct']:+.2f}%")
    print(f"  Avg Loss: {report['avg_loss_pct']:+.2f}%\n")
    
    # Show recent trades
    print("Recent Trades (last 10):")
    for trade in report['trades'][-10:]:
        if trade['type'] == 'BUY':
            print(f"  BUY  {trade['symbol']:8s} @ ${trade['price']:.4f} ({trade['shares']:.6f} shares) "
                  f"Score: {trade['score']:.1f} on {trade['date']}")
        else:
            print(f"  SELL {trade['symbol']:8s} @ ${trade['exit_price']:.4f} "
                  f"Return: {trade['return_pct']:+.2f}% ({trade['reason']}) "
                  f"on {trade['exit_date']}")
    
    # Save report
    output_file = 'trading_simulation_4h_results.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✓ Full report saved to {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
