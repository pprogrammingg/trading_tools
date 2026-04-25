#!/usr/bin/env python3
"""
Fetch hottest trending crypto alt coins (micro/mid cap focus) from CoinGecko.
Outputs: JSON data + HTML table (Currency, MCAP, FDV, Sentiment 1-10), top 10.
Run from technical_analysis/: python scripts/crypto_alt_trends.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None

# Run from technical_analysis/ or scripts/
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "visualizations_output"
COINGECKO_TRENDING = "https://api.coingecko.com/api/v3/search/trending"
COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"

# Cap tiers: focus on alt/micro/mid (exclude mega large)
MCAP_MID_CAP_MAX = 5_000_000_000   # $5B
MCAP_MICRO_PREFER_MAX = 500_000_000  # $500M preferred for "micro"


def _parse_mcap(s: str) -> float:
    """Parse '$1,234,567' or '$1.23B' -> float."""
    if not s or s in ("", "N/A", "null"):
        return 0.0
    s = str(s).strip().replace(",", "").replace("$", "").replace(" ", "")
    if s.endswith("B"):
        return float(s[:-1] or 0) * 1e9
    if s.endswith("M"):
        return float(s[:-1] or 0) * 1e6
    if s.endswith("K"):
        return float(s[:-1] or 0) * 1e3
    try:
        return float(s)
    except ValueError:
        return 0.0


def _fetch(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "trading_tools/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _fetch_trending() -> list:
    data = _fetch(COINGECKO_TRENDING)
    return data.get("coins") or []


def _fetch_markets(ids: list) -> list:
    if not ids:
        return []
    ids_param = ",".join(ids[:50])  # API limit
    url = f"{COINGECKO_MARKETS}?vs_currency=usd&ids={ids_param}&order=market_cap_desc"
    return _fetch(url)


def _sentiment_score(
    trend_rank: int,
    price_change_24h: float | None,
    mcap_usd: float,
    volume_usd: float,
) -> float:
    """
    Composite sentiment 1-10 (10 = extremely hot).
    Uses: trending rank (lower = hotter), 24h % change, volume/MCAP ratio.
    """
    score = 5.0  # base
    # Trending: rank 0 = hottest -> +2.5, rank 6 -> +0.5
    score += max(0, 2.5 - trend_rank * 0.35)
    # 24h % change: e.g. +40% -> +2, -10% -> -0.5
    if price_change_24h is not None:
        score += (price_change_24h / 25.0)  # 25% move ≈ 1 point
    # Volume/MCAP (liquidity/interest): cap effect at 0.5
    if mcap_usd > 0 and volume_usd > 0:
        vol_ratio = volume_usd / mcap_usd
        score += min(0.5, vol_ratio * 2)  # 25% vol/mcap -> +0.5
    return max(1.0, min(10.0, round(score, 1)))


def _build_trending_list() -> list[dict]:
    raw = _fetch_trending()
    ids = []
    by_id = {}
    for i, entry in enumerate(raw):
        item = entry.get("item") or {}
        cid = item.get("id")
        if not cid:
            continue
        data = item.get("data") or {}
        mcap_str = data.get("market_cap") or "$0"
        mcap = _parse_mcap(mcap_str)
        # Prefer micro/mid: exclude rank 1-15 (BTC, ETH, etc. as "not alt" for this list)
        rank = item.get("market_cap_rank") or 999
        if rank is not None and rank <= 15:
            continue
        if mcap > MCAP_MID_CAP_MAX:
            continue
        pct = None
        if isinstance(data.get("price_change_percentage_24h"), dict):
            pct = data["price_change_percentage_24h"].get("usd")
        elif isinstance(data.get("price_change_percentage_24h"), (int, float)):
            pct = data["price_change_percentage_24h"]
        vol_str = data.get("total_volume") or "$0"
        vol = _parse_mcap(vol_str)
        sentiment = _sentiment_score(i, pct, mcap, vol)
        by_id[cid] = {
            "id": cid,
            "symbol": (item.get("symbol") or "").upper(),
            "name": item.get("name") or cid,
            "currency": "USD",
            "market_cap": mcap,
            "fully_diluted_valuation": None,  # filled from markets if we call it
            "market_cap_rank": rank,
            "price_change_24h": pct,
            "sentiment_score": sentiment,
            "trend_rank": i,
        }
        ids.append(cid)

    # Enrich with FDV from markets API (optional)
    try:
        markets = _fetch_markets(ids)
        for m in markets:
            cid = m.get("id")
            if cid in by_id:
                by_id[cid]["market_cap"] = float(m.get("market_cap") or 0)
                fdv = m.get("fully_diluted_valuation")
                by_id[cid]["fully_diluted_valuation"] = float(fdv) if fdv is not None else None
                # Recompute sentiment with actual mcap/volume
                vol = float(m.get("total_volume") or 0)
                pct = by_id[cid].get("price_change_24h")
                if m.get("price_change_percentage_24h") is not None:
                    pct = float(m["price_change_percentage_24h"])
                by_id[cid]["sentiment_score"] = _sentiment_score(
                    by_id[cid]["trend_rank"],
                    pct,
                    by_id[cid]["market_cap"],
                    vol,
                )
    except Exception:
        pass

    out = list(by_id.values())
    out.sort(key=lambda x: (-x["sentiment_score"], -x["market_cap"]))
    return out[:10]


def _h(s: str | int | float) -> str:
    """Escape for HTML text."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt_mcap(v: float | None) -> str:
    if v is None or v <= 0:
        return "—"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    if v >= 1e3:
        return f"${v/1e3:.2f}K"
    return f"${v:.2f}"


def main() -> int:
    if urllib is None:
        print("urllib required", file=sys.stderr)
        return 1
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        rows = _build_trending_list()
    except Exception as e:
        print(f"Fetch error: {e}", file=sys.stderr)
        return 1
    # JSON
    data = {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "CoinGecko trending + markets",
        "top_10": [
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "currency": r["currency"],
                "market_cap": r["market_cap"],
                "fully_diluted_valuation": r["fully_diluted_valuation"],
                "sentiment_score": r["sentiment_score"],
            }
            for r in rows
        ],
    }
    json_path = OUTPUT_DIR / "crypto_alt_trends.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # HTML table
    headers = ["#", "Symbol", "Name", "Currency", "MCAP", "FDV", "Sentiment (1–10)"]
    table_rows = []
    for i, r in enumerate(rows, 1):
        table_rows.append([
            str(i),
            r["symbol"],
            r["name"],
            r["currency"],
            _fmt_mcap(r["market_cap"]),
            _fmt_mcap(r.get("fully_diluted_valuation")),
            str(r["sentiment_score"]),
        ])
    html_table = _build_table_html(headers, table_rows)
    html_content = _build_page(html_table, data.get("as_of", ""))
    html_path = OUTPUT_DIR / "crypto_alt_trends.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"Wrote {json_path.name} and {html_path.name} (top {len(rows)} micro/mid cap trends)")
    return 0


def _build_table_html(headers: list, rows: list[list]) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for row in rows:
        trs.append("".join(f"<td>{_h(c)}</td>" for c in row))
    return f"""    <table>
        <thead><tr>{th}</tr></thead>
        <tbody>
{"".join(f"        <tr>{tr}</tr>\n" for tr in trs)}        </tbody>
    </table>"""


def _build_page(table_html: str, as_of: str) -> str:
    back = '<a href="index.html" class="back">← Back to Index</a>\n'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Alt Trends – Micro / Mid Cap</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        p.subtitle {{ color: #666; }}
        table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ padding: 10px 12px; text-align: left; border-bottom: 2px solid #ddd; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .link-bar {{ margin: 20px 0; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }}
        .link-bar a {{ padding: 12px 20px; color: white; text-decoration: none; border-radius: 20px; font-weight: bold; }}
        .link-bar a:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
{back}
    <h1>🔥 Hottest Crypto Alt Trends (Micro / Mid Cap)</h1>
    <p class="subtitle">Top 10 by sentiment (CoinGecko trending). Data as of {as_of} UTC. 10 = extremely hot.</p>
{table_html}
</body>
</html>"""


if __name__ == "__main__":
    sys.exit(main())
