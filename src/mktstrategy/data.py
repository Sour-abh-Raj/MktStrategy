from __future__ import annotations

import csv
import random
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO, TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

NSE_ARCHIVE = "https://nsearchives.nseindia.com/content/historical/DERIVATIVES"


@dataclass
class DownloadStats:
    downloaded: int
    skipped: int
    failed: int


def _fo_url(trade_date: date) -> str:
    month = trade_date.strftime("%b").upper()
    stamp = trade_date.strftime("%d%b%Y").upper()
    return f"{NSE_ARCHIVE}/{trade_date.year}/{month}/fo{stamp}bhav.csv.zip"


def _request(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read()


def download_fo_bhavcopy(start: date, end: date, out_dir: str | Path) -> DownloadStats:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    current = start
    downloaded = skipped = failed = 0
    while current <= end:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        output_file = out / f"fo_{current.isoformat()}.csv"
        if output_file.exists():
            skipped += 1
            current += timedelta(days=1)
            continue

        try:
            blob = _request(_fo_url(current))
            with ZipFile(BytesIO(blob)) as zf:
                csv_names = [x for x in zf.namelist() if x.endswith(".csv")]
                if not csv_names:
                    raise ValueError("no csv in zip")
                with zf.open(csv_names[0]) as src, output_file.open("w", encoding="utf-8") as dst:
                    dst.write(TextIOWrapper(src, encoding="utf-8", errors="replace").read())
            downloaded += 1
        except Exception:
            failed += 1

        current += timedelta(days=1)

    return DownloadStats(downloaded=downloaded, skipped=skipped, failed=failed)


def parse_float(x: str) -> float | None:
    try:
        return float(x)
    except Exception:
        return None


def parse_date(x: str) -> datetime | None:
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(x.strip(), fmt)
        except Exception:
            pass
    return None


def load_fo_dataset(data_dir: str | Path) -> list[dict]:
    files = sorted(Path(data_dir).glob("fo_*.csv"))
    if not files:
        raise FileNotFoundError(f"No FO files found in {data_dir}")

    rows: list[dict] = []
    for fp in files:
        with fp.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                row = {str(k).strip().upper(): (v.strip() if isinstance(v, str) else v) for k, v in r.items()}
                ts = parse_date(row.get("TIMESTAMP", ""))
                exp = parse_date(row.get("EXPIRY_DT", ""))
                if not ts or not exp:
                    continue
                row["TIMESTAMP"] = ts
                row["EXPIRY_DT"] = exp
                for k in ["STRIKE_PR", "CLOSE", "OPEN_INT", "CHG_IN_OI", "IMP_VOLT", "UNDERLYING"]:
                    row[k] = parse_float(str(row.get(k, "")))
                if any(row[k] is None for k in ["STRIKE_PR", "CLOSE", "OPEN_INT", "CHG_IN_OI", "IMP_VOLT", "UNDERLYING"]):
                    continue
                rows.append(row)
    return rows


def generate_synthetic_fo_data(start: date, end: date) -> list[dict]:
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "LT", "ITC"]
    shifts = (-0.08, -0.04, 0.0, 0.04, 0.08)
    rows: list[dict] = []
    random.seed(7)

    contracts: dict[tuple[str, str], list[float]] = {}
    state: dict[tuple[str, str, float], dict] = {}
    for sym in symbols:
        base_spot = random.uniform(700, 2800)
        for typ in ("CE", "PE"):
            strikes = [round(base_spot * (1 + s), -1) for s in shifts]
            contracts[(sym, typ)] = strikes
            for strike in strikes:
                state[(sym, typ, strike)] = {
                    "spot": base_spot,
                    "close": max(20.0, random.gauss(120, 30)),
                    "oi": max(30000.0, random.gauss(200000, 50000)),
                    "iv": max(8.0, random.gauss(23, 3)),
                }

    current = start
    while current <= end:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue
        ts = datetime.combine(current, datetime.min.time())

        for sym in symbols:
            expiry = datetime.combine(end, datetime.min.time())
            for typ in ("CE", "PE"):
                for strike in contracts[(sym, typ)]:
                    s = state[(sym, typ, strike)]
                    s["spot"] = max(50.0, s["spot"] * (1 + random.gauss(0, 0.004)))
                    chg_oi = random.gauss(0, 10000)
                    s["oi"] = max(1000.0, s["oi"] + chg_oi)
                    s["iv"] = max(5.0, s["iv"] + random.gauss(0, 0.8))
                    s["close"] = max(1.0, s["close"] * (1 + random.gauss(0, 0.06)))

                    if random.random() < 0.03:
                        jump = random.uniform(60000, 120000)
                        chg_oi += jump
                        s["oi"] += jump
                        s["iv"] += random.uniform(8, 18)
                        s["close"] *= random.uniform(1.08, 1.35)

                    rows.append(
                        {
                            "INSTRUMENT": "OPTSTK",
                            "SYMBOL": sym,
                            "TIMESTAMP": ts,
                            "EXPIRY_DT": expiry,
                            "STRIKE_PR": strike,
                            "OPTION_TYP": typ,
                            "CLOSE": s["close"],
                            "OPEN_INT": s["oi"],
                            "CHG_IN_OI": chg_oi,
                            "IMP_VOLT": s["iv"],
                            "UNDERLYING": s["spot"],
                        }
                    )
        current += timedelta(days=1)
    return rows
