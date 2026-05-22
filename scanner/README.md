# Weekly EMA(9)/EMA(21) Crossover Scanner

Scans all US (NYSE/NASDAQ/AMEX) + Canadian (TSX/TSXV) equities for the
classic bullish trigger: weekly EMA(9) has just crossed above weekly
EMA(21) — i.e. `EMA9 > EMA21` on the most recent weekly bar AND
`EMA9 <= EMA21` on the prior bar.

Data source: [EODHD](https://eodhd.com). EODHD is used because it is the
only one of the three configured providers with full TSX/TSXV coverage
and weekly OHLC history in a single endpoint.

## Setup

```bash
cd scanner
pip install -r requirements.txt
cp ../.env.example ../.env
# edit ../.env and set EODHD_API_KEY=...
```

> The `.env` file is gitignored. Never commit API keys.

## Run

```bash
python ema_crossover_scan.py
```

Useful flags:

| Flag           | Default       | Notes                                        |
| -------------- | ------------- | -------------------------------------------- |
| `--exchanges`  | `US TO V`     | EODHD exchange codes                         |
| `--workers`    | `12`          | Parallel HTTP workers                        |
| `--limit N`    | _all_         | Cap symbols (smoke-test)                     |
| `--out PATH`   | auto         | Output CSV path                              |

Smoke test the wiring first:

```bash
python ema_crossover_scan.py --exchanges US --limit 100 --workers 4
```

## Output

CSV at `scanner/output/crossovers_<UTC-date>.csv` with columns:

```
symbol, name, exchange, week_date, close, ema9, ema21, prev_ema9, prev_ema21
```

Matches are also streamed to stdout as they are detected.

## Notes & caveats

- **Current week is live.** The most recent weekly bar updates intraday,
  so a crossover detected mid-week may flip before Friday close. Re-run
  Friday evening (or Saturday) for a settled signal.
- **Universe size.** US+TO+V is ~10k–13k tradable equities and ETFs.
  Expect one API call per symbol plus three universe calls. At the
  default 12 workers the scan typically takes 15–30 minutes and uses
  ~12k–14k EODHD daily API credits. Confirm your plan's quota.
- **EMA seeding.** EMAs are seeded with the SMA of the first 9/21 values
  (TradingView-compatible). Symbols with fewer than 30 weekly bars are
  skipped.
- **Adjusted closes** are preferred (handles splits/dividends).
- **Other providers.** Unusual Whales is geared to options flow, not
  bulk equity OHLC. Polygon.io (formerly Massive) has excellent US
  equity data but no native TSX/TSXV coverage, so it would only handle
  the American side of the scan. Neither is wired up here. If you want
  Polygon as a cross-check on the US side or to reduce EODHD quota
  usage, ping me — it's a small addition.
