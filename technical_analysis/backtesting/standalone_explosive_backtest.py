#!/usr/bin/env python3
"""
Standalone Explosive Moves Backtest
Tests PI Indicator, Hash Ribbon, and validates scoring system
Doesn't require full technical_analysis module imports
"""

import json
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
import numpy as np


def load_symbols_config():
    """Load symbols from config"""
    with open('symbols_config.json', 'r') as f:
        return json.load(f)


def calculate_price_intensity(close, volume, period=14):
    """Price Intensity Indicator - Fixed calculation"""
    if len(close) < period * 4:
        return None
    
    try:
        # Price momentum (rate of change)
        momentum = close.pct_change(period).abs()
        
        # Volume strength (current volume vs average)
        volume_ma = volume.rolling(window=period).mean()
        volume_strength = volume / (volume_ma + 0.0001)  # Avoid division by zero
        
        # Volatility compression (low volatility = potential explosion)
        volatility = close.rolling(window=period).std()
        volatility_ma = volatility.rolling(window=period * 2).mean()
        volatility_compression = volatility_ma / (volatility + 0.0001)  # Inverse: low vol = high compression
        
        # Price extension (how far from moving average)
        price_ma = close.rolling(window=period * 2).mean()
        price_extension = abs((close - price_ma) / (price_ma + 0.0001)) + 0.01
        
        # Combine into PI
        pi = (momentum * volume_strength * volatility_compression) / price_extension
        
        # Normalize to 0-100 scale using rolling min/max
        pi_min = pi.rolling(window=period * 4, min_periods=1).min()
        pi_max = pi.rolling(window=period * 4, min_periods=1).max()
        pi_range = pi_max - pi_min + 0.0001
        
        pi_normalized = ((pi - pi_min) / pi_range) * 100
        
        # Return last value
        if len(pi_normalized) > 0:
            return pi_normalized.iloc[-1] if not pd.isna(pi_normalized.iloc[-1]) else None
        return None
    except Exception as e:
        return None


def find_explosive_moves(df, min_move_pct=30, lookback_days=60):
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


def calculate_simple_score(df_entry, category, pi_value=None):
    """
    Simplified scoring system for backtesting
    Returns score and key indicators
    Includes explosive move setup detection
    """
    if len(df_entry) < 50:
        return 0, {}
    
    close = df_entry['Close']
    high = df_entry['High']
    low = df_entry['Low']
    volume = df_entry['Volume']
    
    score = 0
    indicators = {}
    breakdown = {}
    
    # RSI (simplified)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    indicators['rsi'] = round(rsi_value, 2)
    
    # Category-specific RSI logic
    is_crypto = category == "cryptocurrencies"
    is_tech = category in ["tech_stocks", "faang_hot_stocks", "semiconductors"]
    use_mean_reversion = is_crypto or is_tech
    
    if use_mean_reversion:
        if rsi_value > 70:
            score += 1
            breakdown['rsi_overbought_mean_reversion'] = 1
        elif rsi_value < 30:
            score -= 1.5
            breakdown['rsi_oversold_avoid'] = -1.5
    else:
        if rsi_value < 30:
            score += 2
            breakdown['rsi_oversold'] = 2
        elif rsi_value > 70:
            score -= 2
            breakdown['rsi_overbought'] = -2
    
    # Moving averages
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    sma50 = close.rolling(window=50).mean()
    sma200 = close.rolling(window=200).mean()
    
    current_price = close.iloc[-1]
    indicators['ema50'] = round(ema50.iloc[-1], 2) if len(ema50) > 0 else None
    indicators['ema200'] = round(ema200.iloc[-1], 2) if len(ema200) > 0 else None
    
    if indicators['ema50'] and current_price > indicators['ema50']:
        score += 0.5
        breakdown['price_above_ema50'] = 0.5
    if indicators['ema200'] and current_price > indicators['ema200']:
        score += 1
        breakdown['price_above_ema200'] = 1
    
    # Golden Cross
    if len(sma50) > 0 and len(sma200) > 0:
        if sma50.iloc[-1] > sma200.iloc[-1]:
            score += 1.5
            breakdown['golden_cross'] = 1.5
    
    # ADX (simplified)
    try:
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=14).mean()
        
        adx_value = adx.iloc[-1] if len(adx) > 0 and not pd.isna(adx.iloc[-1]) else None
        indicators['adx'] = round(adx_value, 2) if adx_value else None
        indicators['adx_series'] = adx  # Store full series for rising detection
    except:
        indicators['adx_series'] = None
        pass
    
    # Momentum
    if len(close) >= 14:
        momentum = ((close.iloc[-1] / close.iloc[-14]) - 1) * 100
        indicators['momentum'] = round(momentum, 2)
        if momentum > 8:
            score += 0.5
            breakdown['strong_momentum'] = 0.5
    
    # Overextension penalty (only if price is extended AND not in explosive setup)
    explosive_setup_detected = False
    
    # EXPLOSIVE MOVE SETUP DETECTION
    # Check for volatility compression
    volatility = close.rolling(window=20).std()
    volatility_ma = volatility.rolling(window=40).mean()
    volatility_compressed = volatility.iloc[-1] < volatility_ma.iloc[-1] * 0.7 if len(volatility) > 0 and len(volatility_ma) > 0 else False
    
    # Check for volume building
    volume_ma_short = volume.rolling(window=10).mean()
    volume_ma_long = volume.rolling(window=30).mean()
    volume_building = volume_ma_short.iloc[-1] > volume_ma_long.iloc[-1] * 1.1 if len(volume_ma_short) > 0 and len(volume_ma_long) > 0 else False
    
    # Check for price near support
    recent_low = close.rolling(window=20).min()
    near_support = current_price <= recent_low.iloc[-1] * 1.05 if len(recent_low) > 0 else False
    
    # Check for ADX rising from low base
    adx_rising = False
    adx_series = indicators.get('adx_series')
    if adx_value and adx_series is not None and len(adx_series) >= 5:
        try:
            adx_current = adx_series.iloc[-1]
            adx_5_ago = adx_series.iloc[-5]
            # ADX rising if it increased by at least 5% and is >= 20
            adx_rising = (adx_current > adx_5_ago * 1.05) and (adx_current >= 20)
        except:
            adx_rising = False
    
    # Explosive setup: multiple conditions align
    setup_conditions = sum([volatility_compressed, volume_building, near_support, adx_rising])
    if setup_conditions >= 3:
        explosive_setup_detected = True
        score += 3.0
        breakdown['explosive_move_setup'] = 3.0
        indicators['explosive_setup'] = True
    
    # IMPROVED OVERSOLD HANDLING
    # If oversold BUT in explosive setup, give bonus instead of penalty
    if use_mean_reversion:
        if 30 <= rsi_value <= 40:  # Mildly oversold
            if explosive_setup_detected or adx_rising:
                score += 1.5  # Bonus for oversold + setup
                breakdown['oversold_explosive_setup'] = 1.5
            elif rsi_value > 70:
                score += 1
                breakdown['rsi_overbought_mean_reversion'] = 1
        elif rsi_value < 30:  # Very oversold
            if explosive_setup_detected:
                score += 1.0  # Still bonus if in setup
                breakdown['very_oversold_explosive_setup'] = 1.0
            else:
                score -= 1.5
                breakdown['rsi_oversold_avoid'] = -1.5
    
    # ADX RISING FROM LOW BASE (very bullish)
    if adx_rising:
        if 20 <= adx_value <= 25:
            score += 2.5
            breakdown['adx_rising_from_low'] = 2.5
        elif 25 < adx_value <= 30:
            score += 2.0
            breakdown['adx_rising_strong'] = 2.0
        elif adx_value > 30:
            score += 2.5
            breakdown['adx_rising_very_strong'] = 2.5
    
    # VOLUME SURGE DETECTION
    if volume_building:
        score += 1.5
        breakdown['volume_building'] = 1.5
    
    # Volume surge during consolidation
    if len(volume) >= 20:
        avg_volume = volume.rolling(window=20).mean()
        if volume.iloc[-1] > avg_volume.iloc[-1] * 1.5 and volatility_compressed:
            score += 1.5
            breakdown['volume_surge_consolidation'] = 1.5
    
    # Overextension penalty (only if NOT in explosive setup)
    if not explosive_setup_detected and indicators['ema50'] and current_price > indicators['ema50']:
        extension_pct = ((current_price / indicators['ema50']) - 1) * 100
        if extension_pct > 30:
            penalty = -1 * (0.5 if is_crypto else 0.75 if is_tech else 1.0)
            score += penalty
            breakdown['overextension'] = round(penalty, 1)
    
    # PI INDICATOR INTEGRATION
    if pi_value is not None and not pd.isna(pi_value):
        if pi_value > 70:
            score += 2.0
            breakdown['pi_high'] = 2.0
        elif pi_value > 50:
            score += 1.0
            breakdown['pi_moderate'] = 1.0
        indicators['pi'] = round(pi_value, 2)
    
    return round(score, 1), {'indicators': indicators, 'breakdown': breakdown}


def backtest_symbol(symbol, category, min_move_pct=30):
    """Backtest a single symbol"""
    print(f"  Testing {symbol} ({category})...")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        if df is None or len(df) < 100:
            print(f"    ✗ Insufficient data")
            return None
        
        # Resample to weekly
        df_weekly = df.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        if len(df_weekly) < 50:
            print(f"    ✗ Insufficient data after resampling")
            return None
        
        # Find explosive moves
        explosive_moves = find_explosive_moves(df_weekly, min_move_pct=min_move_pct)
        
        if len(explosive_moves) == 0:
            print(f"    ✗ No explosive moves found (>{min_move_pct}% within 60 days)")
            return None
        
        print(f"    ✓ Found {len(explosive_moves)} explosive move(s)")
        
        results = []
        for move in explosive_moves:
            entry_date = move['entry_date']
            entry_idx = df_weekly.index.get_loc(entry_date)
            
            if entry_idx < 50:
                continue
            
            df_test = df_weekly.iloc[:entry_idx+1].copy()
            
            try:
                # Calculate PI FIRST (needed for scoring)
                pi_value = None
                if len(df_test) >= 56:  # Need at least 4 periods for normalization
                    pi_value = calculate_price_intensity(df_test['Close'], df_test['Volume'])
                
                # Calculate score (now includes PI)
                score, score_data = calculate_simple_score(df_test, category, pi_value=pi_value)
                
                results.append({
                    'symbol': symbol,
                    'category': category,
                    'entry_date': str(entry_date),
                    'entry_price': move['entry_price'],
                    'peak_date': str(move['peak_date']),
                    'peak_price': move['peak_price'],
                    'return_pct': move['return_pct'],
                    'days_to_peak': move['days_to_peak'],
                    'score_at_entry': score,
                    'pi_value': pi_value,
                    'indicators': score_data['indicators'],
                    'score_breakdown': score_data['breakdown']
                })
            except Exception as e:
                continue
        
        return results
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None


def main():
    """Run backtest"""
    print("="*80)
    print("EXPLOSIVE MOVES BACKTEST")
    print("Testing PI Indicator and Scoring System")
    print("="*80)
    
    symbols_config = load_symbols_config()
    all_results = {}
    
    # Test one stock per category
    for category, symbols in symbols_config.items():
        if len(symbols) == 0:
            continue
        print(f"\n{category.upper()}:")
        for symbol in symbols[:2]:  # Test 2 per category
            results = backtest_symbol(symbol, category, min_move_pct=30)
            if results:
                all_results[(symbol, category)] = results
    
    # Analyze
    total_moves = sum(len(r) for r in all_results.values())
    high_score_moves = sum(1 for r in all_results.values() for m in r if m['score_at_entry'] >= 6)
    good_score_moves = sum(1 for r in all_results.values() for m in r if m['score_at_entry'] >= 4)
    
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    print(f"Total Explosive Moves: {total_moves}")
    print(f"Moves with High Score (>=6): {high_score_moves} ({high_score_moves/total_moves*100:.1f}%)" if total_moves > 0 else "N/A")
    print(f"Moves with Good Score (>=4): {good_score_moves} ({good_score_moves/total_moves*100:.1f}%)" if total_moves > 0 else "N/A")
    
    # Best opportunities
    all_moves = [m for r in all_results.values() for m in r]
    all_moves.sort(key=lambda x: x['return_pct'], reverse=True)
    
    print("\n" + "="*80)
    print("TOP 10 BEST BUY OPPORTUNITIES")
    print("="*80)
    for i, move in enumerate(all_moves[:10], 1):
        print(f"\n{i}. {move['symbol']} ({move['category']})")
        print(f"   Entry: {move['entry_date']} @ ${move['entry_price']:.2f}")
        print(f"   Peak: {move['peak_date']} @ ${move['peak_price']:.2f}")
        print(f"   Return: {move['return_pct']:.2f}% in {move['days_to_peak']} days")
        print(f"   Score: {move['score_at_entry']:.1f}")
        print(f"   PI: {move.get('pi_value', 'N/A')}")
        print(f"   RSI: {move['indicators'].get('rsi', 'N/A')}, ADX: {move['indicators'].get('adx', 'N/A')}")
    
    # Save results
    with open('explosive_moves_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_moves': total_moves,
            'high_score_moves': high_score_moves,
            'good_score_moves': good_score_moves,
            'best_opportunities': all_moves[:20]
        }, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to explosive_moves_results.json")


if __name__ == "__main__":
    main()
