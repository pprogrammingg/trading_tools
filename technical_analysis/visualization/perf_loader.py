"""
Relative performance vs SPY for visualization. Cached; parallel yfinance fetches when allowed.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def _spy_row(sym: str, r_spy_1m: float, r_spy_1w: float) -> Dict[str, Optional[float]]:
    try:
        import pandas as pd
        import yfinance as yf
    except ImportError:
        return {"1M_vs_spy": None, "1W_vs_spy": None}
    try:
        df = yf.download(
            sym, period="60d", interval="1d", progress=False, auto_adjust=False, threads=False
        )
        if df is None or len(df) < 5:
            return {"1M_vs_spy": None, "1W_vs_spy": None}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df["Close"].dropna()
        if len(close) < 5:
            return {"1M_vs_spy": None, "1W_vs_spy": None}
        r_sym_1m = (close.iloc[-1] / close.iloc[-min(30, len(close))] - 1) * 100
        r_sym_1w = (close.iloc[-1] / close.iloc[-min(5, len(close))] - 1) * 100
        vs_spy_1m = ((1 + r_sym_1m / 100) / (1 + r_spy_1m / 100) - 1) * 100
        vs_spy_1w = ((1 + r_sym_1w / 100) / (1 + r_spy_1w / 100) - 1) * 100
        return {
            "1M_vs_spy": round(vs_spy_1m, 2),
            "1W_vs_spy": round(vs_spy_1w, 2),
        }
    except Exception:
        return {"1M_vs_spy": None, "1W_vs_spy": None}


def load_performance_vs_spy(
    symbols: Set[str],
    cache_dir: Path,
    max_age_days: int = 1,
    allow_network: bool = True,
    max_workers: int = 8,
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    1M and 1W return vs SPY (%), cached in result_scores/performance_vs_spy.json.
    When allow_network is False: return slice from any cached file, no yfinance.
    (max_age_days reserved for future stale-refresh; daily cache key remains as-of today.)
    """
    del max_age_days  # same behavior as historical visualize_scores
    if not symbols:
        return {}
    cache_path = cache_dir / "performance_vs_spy.json"
    today = time.strftime("%Y-%m-%d")
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache: Dict[str, Any] = json.load(f)
            data = cache.get("data")
            if isinstance(data, dict) and not allow_network:
                return {k: data.get(k) or {"1M_vs_spy": None, "1W_vs_spy": None} for k in symbols}
            if cache.get("as_of") == today and data:
                return {k: v for k, v in data.items() if k in symbols}
        except Exception:
            pass
    if not allow_network:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    try:
        import pandas as pd
        import yfinance as yf
    except ImportError:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    spy = yf.download("SPY", period="60d", interval="1d", progress=False, auto_adjust=False, threads=False)
    if spy is None or len(spy) < 30:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    close_spy = spy["Close"].dropna()
    if len(close_spy) < 30:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    r_spy_1m = (close_spy.iloc[-1] / close_spy.iloc[-min(30, len(close_spy))] - 1) * 100
    r_spy_1w = (close_spy.iloc[-1] / close_spy.iloc[-min(5, len(close_spy))] - 1) * 100
    out: Dict[str, Dict[str, Optional[float]]] = {}
    sym_list: List[str] = list(symbols)[:300]
    if not sym_list:
        return {}
    workers = min(max(1, max_workers), 16, len(sym_list))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_spy_row, s, r_spy_1m, r_spy_1w): s for s in sym_list}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                out[s] = fut.result()
            except Exception:
                out[s] = {"1M_vs_spy": None, "1W_vs_spy": None}
    for s in sym_list:
        if s not in out:
            out[s] = {"1M_vs_spy": None, "1W_vs_spy": None}
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump({"as_of": today, "data": out}, f, indent=0)
    except Exception:
        pass
    return {k: v for k, v in out.items() if k in symbols}
