"""
Unified Backtesting Framework
Robust, reusable framework for testing scoring systems and optimizing parameters
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import PI calculation for backtest framework
try:
    from scoring.improved_scoring import calculate_price_intensity
except ImportError:
    try:
        from improved_scoring import calculate_price_intensity
    except ImportError:
        def calculate_price_intensity(close, volume, period=14):
            return None


class BacktestFramework:
    """Unified backtesting framework for scoring system optimization"""
    
    def __init__(self, scoring_function: Callable, symbols_config: Dict):
        """
        Initialize backtest framework
        
        Args:
            scoring_function: Function that takes (df, category) and returns score dict
            symbols_config: Dictionary of category -> list of symbols
        """
        self.scoring_function = scoring_function
        self.symbols_config = symbols_config
        self.results_cache = {}
    
    def download_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Download historical data with error handling"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            if df is None or len(df) == 0:
                return None
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            return df
        except Exception as e:
            return None
    
    def resample_to_timeframe(self, df: pd.DataFrame, timeframe: str = "1W") -> pd.DataFrame:
        """Resample data to specified timeframe"""
        if timeframe == "2D":
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
            df_resampled = df.resample('M').agg({
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
    
    def find_explosive_moves(
        self, 
        df: pd.DataFrame, 
        min_move_pct: float = 30, 
        lookback_days: int = 60
    ) -> List[Dict]:
        """Find explosive moves in historical data"""
        explosive_moves = []
        
        for i in range(lookback_days, len(df) - 10):
            current_price = df['Close'].iloc[i]
            future_prices = df['Close'].iloc[i+1:i+lookback_days+1]
            
            if len(future_prices) == 0:
                continue
            
            max_future_price = future_prices.max()
            max_future_idx = future_prices.idxmax()
            return_pct = ((max_future_price / current_price) - 1) * 100
            
            if return_pct >= min_move_pct:
                explosive_moves.append({
                    'entry_date': df.index[i],
                    'entry_price': current_price,
                    'peak_date': max_future_idx,
                    'peak_price': max_future_price,
                    'return_pct': return_pct,
                    'days_to_peak': (max_future_idx - df.index[i]).days
                })
        
        return explosive_moves
    
    def backtest_symbol(
        self,
        symbol: str,
        category: str,
        min_move_pct: float = 30,
        timeframe: str = "1W",
        min_data_points: int = 50
    ) -> Optional[List[Dict]]:
        """Backtest a single symbol"""
        # Download data
        df = self.download_data(symbol, period="2y")
        if df is None or len(df) < min_data_points:
            return None
        
        # Resample
        df_resampled = self.resample_to_timeframe(df, timeframe)
        if len(df_resampled) < min_data_points:
            return None
        
        # Find explosive moves
        explosive_moves = self.find_explosive_moves(df_resampled, min_move_pct=min_move_pct)
        if len(explosive_moves) == 0:
            return None
        
        results = []
        
        for move in explosive_moves:
            entry_date = move['entry_date']
            entry_idx = df_resampled.index.get_loc(entry_date)
            
            if entry_idx < min_data_points:
                continue
            
            df_test = df_resampled.iloc[:entry_idx+1].copy()
            
            try:
                # Calculate score using provided function
                # Handle both old signature (df, category) and new (df, category, pi_value)
                import inspect
                sig = inspect.signature(self.scoring_function)
                if len(sig.parameters) == 3:
                    # New signature with pi_value
                    pi_value = calculate_price_intensity(df_test['Close'], df_test['Volume']) if 'calculate_price_intensity' in globals() else None
                    score_result = self.scoring_function(df_test, category, pi_value)
                else:
                    score_result = self.scoring_function(df_test, category)
                
                results.append({
                    'symbol': symbol,
                    'category': category,
                    'entry_date': str(entry_date),
                    'entry_price': move['entry_price'],
                    'peak_date': str(move['peak_date']),
                    'peak_price': move['peak_price'],
                    'return_pct': move['return_pct'],
                    'days_to_peak': move['days_to_peak'],
                    'score_at_entry': score_result.get('score', 0),
                    'indicators': score_result.get('indicators', {}),
                    'score_breakdown': score_result.get('breakdown', {})
                })
            except Exception as e:
                continue
        
        return results if results else None
    
    def run_backtest(
        self,
        categories: Optional[List[str]] = None,
        symbols_per_category: int = 3,
        min_move_pct: float = 30
    ) -> Dict:
        """Run comprehensive backtest across categories"""
        if categories is None:
            categories = list(self.symbols_config.keys())
        
        all_results = {}
        
        for category in categories:
            if category not in self.symbols_config:
                continue
            
            symbols = self.symbols_config[category][:symbols_per_category]
            
            for symbol in symbols:
                results = self.backtest_symbol(symbol, category, min_move_pct=min_move_pct)
                if results:
                    all_results[(symbol, category)] = results
        
        return all_results
    
    def analyze_results(self, all_results: Dict) -> Dict:
        """Analyze backtest results"""
        analysis = {
            'total_explosive_moves': 0,
            'moves_with_high_score': 0,  # Score >= 6
            'moves_with_good_score': 0,  # Score >= 4
            'moves_with_ok_score': 0,  # Score >= 2
            'moves_with_low_score': 0,  # Score < 2
            'avg_return_by_score': defaultdict(list),
            'category_performance': defaultdict(lambda: {
                'total': 0,
                'high_score': 0,
                'good_score': 0,
                'avg_return_high': [],
                'avg_return_good': []
            }),
            'best_opportunities': []
        }
        
        for result_list in all_results.values():
            if not result_list:
                continue
            
            for move in result_list:
                analysis['total_explosive_moves'] += 1
                score = move['score_at_entry']
                return_pct = move['return_pct']
                category = move['category']
                
                # Score buckets
                if score >= 6:
                    analysis['moves_with_high_score'] += 1
                    analysis['avg_return_by_score']['high'].append(return_pct)
                    analysis['category_performance'][category]['high_score'] += 1
                    analysis['category_performance'][category]['avg_return_high'].append(return_pct)
                elif score >= 4:
                    analysis['moves_with_good_score'] += 1
                    analysis['avg_return_by_score']['good'].append(return_pct)
                    analysis['category_performance'][category]['good_score'] += 1
                    analysis['category_performance'][category]['avg_return_good'].append(return_pct)
                elif score >= 2:
                    analysis['moves_with_ok_score'] += 1
                    analysis['avg_return_by_score']['ok'].append(return_pct)
                else:
                    analysis['moves_with_low_score'] += 1
                    analysis['avg_return_by_score']['low'].append(return_pct)
                
                analysis['category_performance'][category]['total'] += 1
                
                # Track best opportunities
                if score >= 2:
                    analysis['best_opportunities'].append(move)
        
        # Calculate averages
        for key in analysis['avg_return_by_score']:
            if analysis['avg_return_by_score'][key]:
                analysis['avg_return_by_score'][key] = np.mean(analysis['avg_return_by_score'][key])
        
        # Sort best opportunities
        analysis['best_opportunities'].sort(key=lambda x: x['return_pct'], reverse=True)
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Print comprehensive analysis"""
        total = analysis['total_explosive_moves']
        if total == 0:
            print("No explosive moves found.")
            return
        
        print("\n" + "="*80)
        print("BACKTEST ANALYSIS")
        print("="*80)
        print(f"\nTotal Explosive Moves: {total}")
        print(f"  High Score (>=6): {analysis['moves_with_high_score']} ({analysis['moves_with_high_score']/total*100:.1f}%)")
        print(f"  Good Score (>=4): {analysis['moves_with_good_score']} ({analysis['moves_with_good_score']/total*100:.1f}%)")
        print(f"  OK Score (>=2): {analysis['moves_with_ok_score']} ({analysis['moves_with_ok_score']/total*100:.1f}%)")
        print(f"  Low Score (<2): {analysis['moves_with_low_score']} ({analysis['moves_with_low_score']/total*100:.1f}%)")
        
        print("\nAverage Returns by Score:")
        for score_level, avg_return in analysis['avg_return_by_score'].items():
            if isinstance(avg_return, (int, float)):
                print(f"  {score_level.capitalize()}: {avg_return:.2f}%")
        
        print("\nCategory Performance:")
        for category, perf in sorted(analysis['category_performance'].items()):
            if perf['total'] > 0:
                high_pct = perf['high_score'] / perf['total'] * 100
                good_pct = perf['good_score'] / perf['total'] * 100
                avg_high = np.mean(perf['avg_return_high']) if perf['avg_return_high'] else 0
                avg_good = np.mean(perf['avg_return_good']) if perf['avg_return_good'] else 0
                print(f"  {category}: {perf['total']} moves, {high_pct:.1f}% high score, {good_pct:.1f}% good score")
                if avg_high > 0:
                    print(f"    Avg return (high score): {avg_high:.2f}%")
                if avg_good > 0:
                    print(f"    Avg return (good score): {avg_good:.2f}%")
        
        print("\n" + "="*80)
        print("TOP 10 BEST OPPORTUNITIES")
        print("="*80)
        for i, opp in enumerate(analysis['best_opportunities'][:10], 1):
            print(f"\n{i}. {opp['symbol']} ({opp['category']})")
            print(f"   Entry: {opp['entry_date']} @ ${opp['entry_price']:.2f}")
            print(f"   Peak: {opp['peak_date']} @ ${opp['peak_price']:.2f}")
            print(f"   Return: {opp['return_pct']:.2f}% in {opp['days_to_peak']} days")
            print(f"   Score: {opp['score_at_entry']:.1f}")
            if 'rsi' in opp['indicators']:
                print(f"   RSI: {opp['indicators']['rsi']}, ADX: {opp['indicators'].get('adx', 'N/A')}")
    
    def save_results(self, analysis: Dict, all_results: Dict, filename: str = "backtest_results.json"):
        """Save backtest results to file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'total_explosive_moves': analysis['total_explosive_moves'],
                'moves_with_high_score': analysis['moves_with_high_score'],
                'moves_with_good_score': analysis['moves_with_good_score'],
                'avg_return_by_score': {k: float(v) if isinstance(v, (int, float)) else v 
                                       for k, v in analysis['avg_return_by_score'].items()},
            },
            'best_opportunities': analysis['best_opportunities'][:20],
            'category_performance': {
                k: {
                    'total': v['total'],
                    'high_score': v['high_score'],
                    'good_score': v['good_score'],
                    'avg_return_high': float(np.mean(v['avg_return_high'])) if v['avg_return_high'] else None,
                    'avg_return_good': float(np.mean(v['avg_return_good'])) if v['avg_return_good'] else None,
                }
                for k, v in analysis['category_performance'].items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        return filename
