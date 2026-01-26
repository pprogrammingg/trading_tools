#!/usr/bin/env python3
"""
DCA Trading Simulation: $5 Increments with 4H and 1D Analysis
Dollar Cost Averaging strategy - buy $5 at good scores, sell at sell signals
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

class DCATradingSimulation:
    def __init__(self, dca_amount=5.0, buy_threshold=6.0, sell_threshold=-2.0, 
                 max_positions_per_symbol=10, use_both_timeframes=True):
        """
        Initialize DCA trading simulation
        
        Args:
            dca_amount: Amount to invest per buy signal ($5)
            buy_threshold: Minimum score to buy
            sell_threshold: Maximum score to sell (negative = sell signal)
            max_positions_per_symbol: Maximum number of DCA positions per symbol
            use_both_timeframes: Use both 4H and 1D timeframes for signals
        """
        self.dca_amount = dca_amount
        self.cash = 0.0  # Start with $0, add $5 per buy
        self.positions = defaultdict(list)  # {symbol: [{'shares': float, 'entry_price': float, 'entry_date': datetime, 'entry_score': float, 'timeframe': str}, ...]}
        self.trades = []  # List of all trades
        self.portfolio_value_history = []  # [(date, portfolio_value)]
        self.total_invested = 0.0  # Track total capital invested
        
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.max_positions_per_symbol = max_positions_per_symbol
        self.use_both_timeframes = use_both_timeframes
        
    def get_portfolio_value(self, current_prices):
        """Calculate total portfolio value"""
        total_value = self.cash
        for symbol, position_list in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                for position in position_list:
                    position_value = position['shares'] * current_price
                    total_value += position_value
        return total_value
    
    def get_total_invested(self):
        """Calculate total amount invested"""
        return self.total_invested
    
    def buy_position(self, symbol, current_price, current_date, score, timeframe):
        """Buy a DCA position ($5 increment)"""
        # Check if we've reached max positions for this symbol
        if len(self.positions[symbol]) >= self.max_positions_per_symbol:
            return False
        
        # Need $5 to buy
        if self.cash < self.dca_amount:
            # Add $5 to cash (DCA strategy - add capital when buying)
            self.cash += self.dca_amount
            self.total_invested += self.dca_amount
        
        # Calculate shares for $5
        shares = self.dca_amount / current_price
        
        # Execute buy
        cost = shares * current_price
        if cost > self.cash:
            return False
        
        self.cash -= cost
        
        # Record position
        position = {
            'shares': shares,
            'entry_price': current_price,
            'entry_date': current_date,
            'entry_score': score,
            'timeframe': timeframe
        }
        self.positions[symbol].append(position)
        
        # Record trade
        trade = {
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': current_price,
            'date': current_date,
            'score': score,
            'timeframe': timeframe,
            'cost': cost,
            'dca_amount': self.dca_amount
        }
        self.trades.append(trade)
        
        return True
    
    def sell_positions(self, symbol, current_price, current_date, reason='signal'):
        """Sell all positions for a symbol"""
        if symbol not in self.positions or len(self.positions[symbol]) == 0:
            return 0
        
        total_proceeds = 0
        positions_sold = 0
        
        for position in self.positions[symbol]:
            shares = position['shares']
            entry_price = position['entry_price']
            entry_date = position['entry_date']
            entry_score = position['entry_score']
            timeframe = position.get('timeframe', 'unknown')
            
            # Calculate proceeds
            proceeds = shares * current_price
            total_proceeds += proceeds
            
            # Calculate return
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
                'timeframe': timeframe,
                'return_pct': return_pct,
                'proceeds': proceeds,
                'reason': reason
            }
            self.trades.append(trade)
            positions_sold += 1
        
        # Add proceeds to cash
        self.cash += total_proceeds
        
        # Remove all positions
        del self.positions[symbol]
        
        return positions_sold
    
    def run_simulation(self, symbols, category, start_date=None, end_date=None):
        """Run DCA trading simulation on symbols"""
        print(f"\n{'='*80}")
        print(f"DCA TRADING SIMULATION: ${self.dca_amount:.2f} per Buy Signal")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Buy Threshold: {self.buy_threshold}, Sell Threshold: {self.sell_threshold}")
        print(f"Timeframes: {'4H + 1D' if self.use_both_timeframes else '4H only'}")
        print(f"Max Positions per Symbol: {self.max_positions_per_symbol}")
        print(f"{'='*80}\n")
        
        # Download data for all symbols
        symbol_data_4h = {}
        symbol_data_1d = {}
        
        for symbol in symbols:
            print(f"Downloading data for {symbol}...", end=" ")
            try:
                ticker = yf.Ticker(symbol)
                
                # Download 4H data
                df_1h = ticker.history(period="60d", interval="1h")
                if len(df_1h) > 0:
                    df_4h = df_1h.resample('4h').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                    if len(df_4h) >= 50:
                        symbol_data_4h[symbol] = df_4h
                
                # Download 1D data (longer history)
                df_1d = ticker.history(period="1y", interval="1d")
                if len(df_1d) >= 50:
                    symbol_data_1d[symbol] = df_1d
                
                if symbol in symbol_data_4h or symbol in symbol_data_1d:
                    print(f"✓ (4H: {len(symbol_data_4h.get(symbol, pd.DataFrame()))}, 1D: {len(symbol_data_1d.get(symbol, pd.DataFrame()))})")
                else:
                    print("✗ (insufficient data)")
            except Exception as e:
                print(f"✗ (error: {e})")
                continue
        
        if len(symbol_data_4h) == 0 and len(symbol_data_1d) == 0:
            print("No data available for any symbols!")
            return None
        
        # Get common date range (use 1D data range as primary)
        all_dates = set()
        for df in symbol_data_1d.values():
            all_dates.update(df.index)
        for df in symbol_data_4h.values():
            all_dates.update(df.index)
        all_dates = sorted(all_dates)
        
        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]
        
        print(f"\nSimulating from {all_dates[0]} to {all_dates[-1]} ({len(all_dates)} periods)\n")
        
        # Get market context
        market_context = get_market_context()
        
        # Run simulation
        for i, current_date in enumerate(all_dates):
            if i < 50:  # Need enough history for indicators
                continue
            
            current_prices = {}
            scores_4h = {}
            scores_1d = {}
            
            # Calculate scores for all symbols on both timeframes
            for symbol in set(list(symbol_data_4h.keys()) + list(symbol_data_1d.keys())):
                # 4H scores
                if symbol in symbol_data_4h:
                    df_4h_historical = symbol_data_4h[symbol][symbol_data_4h[symbol].index <= current_date]
                    if len(df_4h_historical) >= 50:
                        current_price_4h = df_4h_historical['Close'].iloc[-1]
                        if symbol not in current_prices:
                            current_prices[symbol] = current_price_4h
                        try:
                            score_result = improved_scoring(df_4h_historical, category, timeframe="4H", market_context=market_context)
                            scores_4h[symbol] = score_result.get('score', 0)
                        except:
                            scores_4h[symbol] = 0
                
                # 1D scores
                if symbol in symbol_data_1d:
                    df_1d_historical = symbol_data_1d[symbol][symbol_data_1d[symbol].index <= current_date]
                    if len(df_1d_historical) >= 50:
                        current_price_1d = df_1d_historical['Close'].iloc[-1]
                        if symbol not in current_prices:
                            current_prices[symbol] = current_price_1d
                        try:
                            score_result = improved_scoring(df_1d_historical, category, timeframe="1D", market_context=market_context)
                            scores_1d[symbol] = score_result.get('score', 0)
                        except:
                            scores_1d[symbol] = 0
            
            # Check sell signals (negative scores on either timeframe)
            for symbol in list(self.positions.keys()):
                if symbol in current_prices:
                    # Check both timeframes for sell signals
                    should_sell = False
                    if symbol in scores_4h and scores_4h[symbol] <= self.sell_threshold:
                        should_sell = True
                    if symbol in scores_1d and scores_1d[symbol] <= self.sell_threshold:
                        should_sell = True
                    
                    if should_sell:
                        self.sell_positions(symbol, current_prices[symbol], current_date, 'sell_signal')
            
            # Check buy signals (high scores on either timeframe)
            for symbol in set(list(scores_4h.keys()) + list(scores_1d.keys())):
                if symbol not in current_prices:
                    continue
                
                # Check if we should buy based on 4H or 1D signals
                buy_4h = symbol in scores_4h and scores_4h[symbol] >= self.buy_threshold
                buy_1d = symbol in scores_1d and scores_1d[symbol] >= self.buy_threshold
                
                if self.use_both_timeframes:
                    # Buy if either timeframe shows good signal
                    if buy_4h or buy_1d:
                        # Use the timeframe with higher score
                        if buy_4h and buy_1d:
                            timeframe = "4H" if scores_4h[symbol] >= scores_1d[symbol] else "1D"
                            score = max(scores_4h[symbol], scores_1d[symbol])
                        elif buy_4h:
                            timeframe = "4H"
                            score = scores_4h[symbol]
                        else:
                            timeframe = "1D"
                            score = scores_1d[symbol]
                        
                        self.buy_position(symbol, current_prices[symbol], current_date, score, timeframe)
                else:
                    # Only use 4H
                    if buy_4h:
                        self.buy_position(symbol, current_prices[symbol], current_date, scores_4h[symbol], "4H")
            
            # Record portfolio value
            portfolio_value = self.get_portfolio_value(current_prices)
            self.portfolio_value_history.append((current_date, portfolio_value))
        
        # Close all positions at end
        final_prices = {}
        for symbol, df in symbol_data_1d.items():
            if len(df) > 0:
                final_prices[symbol] = df['Close'].iloc[-1]
        for symbol, df in symbol_data_4h.items():
            if symbol not in final_prices and len(df) > 0:
                final_prices[symbol] = df['Close'].iloc[-1]
        
        for symbol in list(self.positions.keys()):
            if symbol in final_prices:
                self.sell_positions(symbol, final_prices[symbol], all_dates[-1], 'end_of_simulation')
        
        return self.generate_report(all_dates)
    
    def generate_report(self, all_dates):
        """Generate trading report"""
        # Calculate final portfolio value
        final_value = self.cash  # All positions closed
        total_invested = self.get_total_invested()
        total_return = ((final_value / total_invested - 1) * 100) if total_invested > 0 else 0
        
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
            closest_value = 0.0
            closest_date = start_date
            invested_at_interval = 0.0
            
            for date, value in self.portfolio_value_history:
                if date <= target_date and date > closest_date:
                    closest_value = value
                    closest_date = date
                    # Count investments made up to this date
                    invested_at_interval = sum(t['dca_amount'] for t in self.trades 
                                             if t['type'] == 'BUY' and t['date'] <= date)
            
            if closest_date > start_date and invested_at_interval > 0:
                interval_return = ((closest_value / invested_at_interval - 1) * 100) if invested_at_interval > 0 else 0
                interval_returns[interval_name] = {
                    'date': closest_date,
                    'value': closest_value,
                    'invested': invested_at_interval,
                    'return_pct': interval_return
                }
        
        # Final return
        interval_returns['final'] = {
            'date': all_dates[-1] if all_dates else datetime.now(),
            'value': final_value,
            'invested': total_invested,
            'return_pct': total_return
        }
        
        # Trade statistics
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        winning_trades = [t for t in sell_trades if t.get('return_pct', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('return_pct', 0) <= 0]
        
        avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
        
        # Count DCA positions
        total_dca_positions = sum(len(positions) for positions in self.positions.values())
        total_dca_buys = len(buy_trades)
        
        report = {
            'dca_amount': self.dca_amount,
            'total_invested': total_invested,
            'final_value': final_value,
            'total_return_pct': total_return,
            'interval_returns': interval_returns,
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_dca_positions': total_dca_buys,
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
    """Run DCA trading simulation"""
    # Select volatile assets (Quantum and Crypto)
    symbols_config = load_symbols_config()
    
    # Quantum stocks
    quantum_symbols = symbols_config.get('quantum', [])[:3]
    
    # Crypto
    crypto_symbols = symbols_config.get('cryptocurrencies', [])[:2]
    
    # Combine
    test_symbols = quantum_symbols + crypto_symbols
    
    if len(test_symbols) == 0:
        print("No symbols found! Check symbols_config.json")
        return
    
    print(f"Selected symbols: {test_symbols}")
    
    # Determine category
    category = 'quantum' if quantum_symbols else 'cryptocurrencies'
    
    # Create DCA simulation
    sim = DCATradingSimulation(
        dca_amount=5.0,
        buy_threshold=6.0,  # Buy when score >= 6
        sell_threshold=-2.0,  # Sell when score <= -2
        max_positions_per_symbol=10,  # Max 10 DCA positions per symbol
        use_both_timeframes=True  # Use both 4H and 1D
    )
    
    # Run simulation
    report = sim.run_simulation(test_symbols, category)
    
    if report is None:
        print("Simulation failed!")
        return
    
    # Print report
    print("\n" + "="*80)
    print("DCA TRADING SIMULATION RESULTS")
    print("="*80 + "\n")
    
    print(f"DCA Amount per Buy: ${report['dca_amount']:.2f}")
    print(f"Total Invested: ${report['total_invested']:.2f}")
    print(f"Final Value: ${report['final_value']:.2f}")
    print(f"Total Return: {report['total_return_pct']:+.2f}%\n")
    
    print("Returns at Intervals:")
    for interval_name, data in report['interval_returns'].items():
        if interval_name != 'final':
            date_str = data['date'].strftime('%Y-%m-%d') if hasattr(data['date'], 'strftime') else str(data['date'])
            print(f"  {interval_name.replace('_', ' ').title():15s}: ${data['value']:.2f} "
                  f"({data['return_pct']:+.2f}%) - Invested: ${data['invested']:.2f} at {date_str}")
    
    final_data = report['interval_returns']['final']
    final_date_str = final_data['date'].strftime('%Y-%m-%d') if hasattr(final_data['date'], 'strftime') else str(final_data['date'])
    print(f"  Final:            : ${final_data['value']:.2f} "
          f"({final_data['return_pct']:+.2f}%) - Invested: ${final_data['invested']:.2f} at {final_date_str}\n")
    
    print("Trade Statistics:")
    print(f"  Total Trades: {report['total_trades']}")
    print(f"  Buy Trades (DCA positions): {report['buy_trades']}")
    print(f"  Sell Trades: {report['sell_trades']}")
    print(f"  Winning Trades: {report['winning_trades']}")
    print(f"  Losing Trades: {report['losing_trades']}")
    print(f"  Win Rate: {report['win_rate']:.1f}%")
    print(f"  Avg Win: {report['avg_win_pct']:+.2f}%")
    print(f"  Avg Loss: {report['avg_loss_pct']:+.2f}%\n")
    
    # Show recent trades
    print("Recent Trades (last 15):")
    for trade in report['trades'][-15:]:
        if trade['type'] == 'BUY':
            date_str = str(trade['date'])[:16] if 'date' in trade else 'N/A'
            print(f"  BUY  {trade['symbol']:8s} @ ${trade['price']:.4f} "
                  f"({trade['shares']:.6f} shares) Score: {trade['score']:.1f} ({trade.get('timeframe', 'N/A')}) "
                  f"on {date_str}")
        else:
            date_str = str(trade['exit_date'])[:16] if 'exit_date' in trade else 'N/A'
            print(f"  SELL {trade['symbol']:8s} @ ${trade['exit_price']:.4f} "
                  f"Return: {trade['return_pct']:+.2f}% ({trade['reason']}) "
                  f"on {date_str}")
    
    # Save report
    output_file = 'dca_trading_simulation_results.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✓ Full report saved to {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
