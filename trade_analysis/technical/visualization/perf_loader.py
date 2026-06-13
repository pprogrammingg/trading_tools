"""
Relative performance vs SPY for visualization. Cached; parallel yfinance fetches when allowed.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from yfinance_quiet import quiet_yfinance, symbol_skips_perf_download, to_float

_PERF_TIMEOUT_S = 20


def _normalize_close_series(df):
    import pandas as pd

    if df is None or len(df) == 0:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    close = df.get("Close")
    if close is None:
        return None
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()


def _spy_row(sym: str, r_spy_1m: float, r_spy_1w: float) -> Dict[str, Optional[float]]:
    if symbol_skips_perf_download(sym):
        return {"1M_vs_spy": None, "1W_vs_spy": None}
    try:
        import yfinance as yf
    except ImportError:
        return {"1M_vs_spy": None, "1W_vs_spy": None}
    try:
        with quiet_yfinance():
            df = yf.download(
                sym,
                period="60d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        close = _normalize_close_series(df)
        if close is None or len(close) < 5:
            return {"1M_vs_spy": None, "1W_vs_spy": None}
        last = to_float(close.iloc[-1])
        base_1m = to_float(close.iloc[-min(30, len(close))])
        base_1w = to_float(close.iloc[-min(5, len(close))])
        if last is None or base_1m is None or base_1w is None or base_1m == 0 or base_1w == 0:
            return {"1M_vs_spy": None, "1W_vs_spy": None}
        r_sym_1m = (last / base_1m - 1) * 100
        r_sym_1w = (last / base_1w - 1) * 100
        vs_spy_1m = ((1 + r_sym_1m / 100) / (1 + r_spy_1m / 100) - 1) * 100
        vs_spy_1w = ((1 + r_sym_1w / 100) / (1 + r_spy_1w / 100) - 1) * 100
        f1 = to_float(vs_spy_1m)
        f2 = to_float(vs_spy_1w)
        return {
            "1M_vs_spy": round(f1, 2) if f1 is not None else None,
            "1W_vs_spy": round(f2, 2) if f2 is not None else None,
        }
    except Exception:
        return {"1M_vs_spy": None, "1W_vs_spy": None}


def _sanitize_perf_entry(entry: Any) -> Dict[str, Optional[float]]:
    if not isinstance(entry, dict):
        return {"1M_vs_spy": None, "1W_vs_spy": None}
    return {
        "1M_vs_spy": to_float(entry.get("1M_vs_spy")),
        "1W_vs_spy": to_float(entry.get("1W_vs_spy")),
    }


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
                return {k: _sanitize_perf_entry(data.get(k)) for k in symbols}
            if cache.get("as_of") == today and data:
                return {k: _sanitize_perf_entry(v) for k, v in data.items() if k in symbols}
        except Exception:
            pass
    if not allow_network:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    try:
        import yfinance as yf
    except ImportError:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    sym_list: List[str] = [s for s in list(symbols)[:300] if not symbol_skips_perf_download(s)]
    if not sym_list:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    with quiet_yfinance():
        spy = yf.download(
            "SPY", period="60d", interval="1d", progress=False, auto_adjust=False, threads=False
        )
    close_spy = _normalize_close_series(spy)
    if close_spy is None or len(close_spy) < 30:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    spy_last = to_float(close_spy.iloc[-1])
    spy_base_1m = to_float(close_spy.iloc[-min(30, len(close_spy))])
    spy_base_1w = to_float(close_spy.iloc[-min(5, len(close_spy))])
    if spy_last is None or spy_base_1m is None or spy_base_1w is None:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    r_spy_1m = (spy_last / spy_base_1m - 1) * 100
    r_spy_1w = (spy_last / spy_base_1w - 1) * 100
    r_spy_1m_f = to_float(r_spy_1m)
    r_spy_1w_f = to_float(r_spy_1w)
    if r_spy_1m_f is None or r_spy_1w_f is None:
        return {s: {"1M_vs_spy": None, "1W_vs_spy": None} for s in symbols}
    out: Dict[str, Dict[str, Optional[float]]] = {}
    workers = min(max(1, max_workers), 16, len(sym_list))
    done = 0
    total = len(sym_list)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_spy_row, s, r_spy_1m_f, r_spy_1w_f): s for s in sym_list}
        for fut in as_completed(futs):
            s = futs[fut]
            done += 1
            if done == 1 or done % 25 == 0 or done == total:
                print(f"  Perf vs SPY: {done}/{total} symbols…", flush=True)
            try:
                out[s] = _sanitize_perf_entry(fut.result(timeout=_PERF_TIMEOUT_S))
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
    return {k: _sanitize_perf_entry(v) for k, v in out.items() if k in symbols}
