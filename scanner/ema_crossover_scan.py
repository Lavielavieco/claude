"""
Weekly EMA(9) over EMA(21) crossover scanner for US + Canadian equities.

Uses EODHD as the data source (best US + TSX/TSXV/CSE coverage among the
configured providers). A match is a ticker where on the most recent weekly
bar EMA9 > EMA21 AND on the prior weekly bar EMA9 <= EMA21.

Usage:
    pip install -r requirements.txt
    cp ../.env.example ../.env  # then fill in EODHD_API_KEY
    python ema_crossover_scan.py

Output: scanner/output/crossovers_<YYYY-MM-DD>.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import requests
from dotenv import load_dotenv


EODHD_BASE = "https://eodhd.com/api"

# Exchanges to scan. EODHD codes:
#   US   = consolidated NYSE + NASDAQ + AMEX + OTC
#   TO   = Toronto Stock Exchange (TSX)
#   V    = TSX Venture Exchange (TSXV)
DEFAULT_EXCHANGES = ("US", "TO", "V")

# Minimum weekly bars required to compute a stable 21-EMA.
MIN_WEEKLY_BARS = 30


@dataclass(frozen=True)
class Ticker:
    code: str       # e.g. "AAPL"
    exchange: str   # e.g. "US", "TO"
    name: str
    type: str       # "Common Stock", "ETF", ...

    @property
    def symbol(self) -> str:
        return f"{self.code}.{self.exchange}"


@dataclass(frozen=True)
class Match:
    symbol: str
    name: str
    exchange: str
    close: float
    ema9: float
    ema21: float
    prev_ema9: float
    prev_ema21: float
    week_date: str


def ema(values: list[float], length: int) -> list[float]:
    """Standard exponential moving average, seeded with the SMA of the
    first `length` values. Returns a list aligned with `values`; entries
    before the seed are filled with NaN-equivalent (None)."""
    if len(values) < length:
        return [None] * len(values)
    k = 2.0 / (length + 1.0)
    out: list[float | None] = [None] * (length - 1)
    seed = sum(values[:length]) / length
    out.append(seed)
    prev = seed
    for v in values[length:]:
        prev = v * k + prev * (1.0 - k)
        out.append(prev)
    return out


def http_get(url: str, params: dict, retries: int = 4) -> requests.Response:
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429:
                # Rate limited — back off and retry.
                time.sleep(delay)
                delay *= 2
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_exc = e
            time.sleep(delay)
            delay *= 2
    assert last_exc is not None
    raise last_exc


def fetch_exchange_symbols(api_key: str, exchange: str) -> list[Ticker]:
    """Returns the full ticker list for an EODHD exchange code."""
    url = f"{EODHD_BASE}/exchange-symbol-list/{exchange}"
    r = http_get(url, {"api_token": api_key, "fmt": "json"})
    raw = r.json()
    tickers = []
    for row in raw:
        t = (row.get("Type") or "").strip()
        # Restrict to equities and ETFs; skip funds, indices, bonds, etc.
        if t not in ("Common Stock", "ETF", "Preferred Stock"):
            continue
        code = (row.get("Code") or "").strip()
        if not code:
            continue
        # EODHD sometimes includes warrants/units encoded with suffixes
        # like "X.WT" or "X.UN" — keep them; they may also crossover.
        tickers.append(Ticker(
            code=code,
            exchange=exchange,
            name=(row.get("Name") or "").strip(),
            type=t,
        ))
    return tickers


def fetch_weekly_closes(api_key: str, symbol: str) -> tuple[list[str], list[float]] | None:
    """Returns (dates, closes) of weekly bars, oldest first. None on failure
    or if the ticker has too little history to evaluate EMA21."""
    url = f"{EODHD_BASE}/eod/{symbol}"
    try:
        r = http_get(url, {
            "api_token": api_key,
            "fmt": "json",
            "period": "w",
            "order": "a",  # ascending, oldest first
        })
    except requests.RequestException:
        return None
    data = r.json()
    if not isinstance(data, list) or len(data) < MIN_WEEKLY_BARS:
        return None
    dates: list[str] = []
    closes: list[float] = []
    for bar in data:
        try:
            closes.append(float(bar["adjusted_close"] if bar.get("adjusted_close") is not None else bar["close"]))
            dates.append(str(bar["date"]))
        except (KeyError, TypeError, ValueError):
            return None
    return dates, closes


def detect_crossover(ticker: Ticker, dates: list[str], closes: list[float]) -> Match | None:
    e9 = ema(closes, 9)
    e21 = ema(closes, 21)
    # Need the last two bars to evaluate a crossover.
    if e9[-1] is None or e21[-1] is None or e9[-2] is None or e21[-2] is None:
        return None
    if e9[-1] > e21[-1] and e9[-2] <= e21[-2]:
        return Match(
            symbol=ticker.symbol,
            name=ticker.name,
            exchange=ticker.exchange,
            close=closes[-1],
            ema9=e9[-1],
            ema21=e21[-1],
            prev_ema9=e9[-2],
            prev_ema21=e21[-2],
            week_date=dates[-1],
        )
    return None


def scan(api_key: str, exchanges: Iterable[str], workers: int, limit: int | None) -> list[Match]:
    universe: list[Ticker] = []
    for ex in exchanges:
        print(f"[universe] fetching ticker list for {ex} ...", file=sys.stderr)
        tickers = fetch_exchange_symbols(api_key, ex)
        print(f"[universe] {ex}: {len(tickers)} tradable instruments", file=sys.stderr)
        universe.extend(tickers)

    if limit is not None:
        universe = universe[:limit]

    print(f"[scan] evaluating {len(universe)} symbols with {workers} workers ...", file=sys.stderr)

    matches: list[Match] = []
    done = 0
    started = time.time()

    def task(t: Ticker) -> Match | None:
        bars = fetch_weekly_closes(api_key, t.symbol)
        if bars is None:
            return None
        return detect_crossover(t, *bars)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(task, t): t for t in universe}
        for fut in as_completed(futures):
            done += 1
            try:
                m = fut.result()
            except Exception as e:
                t = futures[fut]
                print(f"[error] {t.symbol}: {e}", file=sys.stderr)
                continue
            if m is not None:
                matches.append(m)
                print(f"[match] {m.symbol:<14} {m.name[:40]:<40} close={m.close:.2f} ema9={m.ema9:.2f} ema21={m.ema21:.2f}")
            if done % 250 == 0:
                rate = done / max(time.time() - started, 1e-6)
                print(f"[scan] {done}/{len(universe)} processed ({rate:.1f}/s, matches: {len(matches)})", file=sys.stderr)
    return matches


def write_csv(matches: list[Match], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "name", "exchange", "week_date", "close", "ema9", "ema21", "prev_ema9", "prev_ema21"])
        for m in sorted(matches, key=lambda x: x.symbol):
            w.writerow([m.symbol, m.name, m.exchange, m.week_date,
                        f"{m.close:.4f}", f"{m.ema9:.4f}", f"{m.ema21:.4f}",
                        f"{m.prev_ema9:.4f}", f"{m.prev_ema21:.4f}"])


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    api_key = os.environ.get("EODHD_API_KEY", "").strip()
    if not api_key:
        print("error: EODHD_API_KEY is not set (see .env.example)", file=sys.stderr)
        return 2

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exchanges", nargs="+", default=list(DEFAULT_EXCHANGES),
                   help="EODHD exchange codes (default: US TO V)")
    p.add_argument("--workers", type=int, default=12,
                   help="parallel HTTP workers (default: 12)")
    p.add_argument("--limit", type=int, default=None,
                   help="cap total tickers (useful for smoke-testing)")
    p.add_argument("--out", type=Path, default=None,
                   help="output CSV path (default: scanner/output/crossovers_<date>.csv)")
    args = p.parse_args()

    out = args.out or (Path(__file__).resolve().parent / "output" /
                       f"crossovers_{datetime.utcnow():%Y-%m-%d}.csv")

    matches = scan(api_key, args.exchanges, args.workers, args.limit)
    write_csv(matches, out)
    print(f"\nDone. {len(matches)} matches written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
