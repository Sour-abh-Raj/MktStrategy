from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from statistics import mean
from typing import Iterable


NSE_BASE = "https://www.nseindia.com"


@dataclass
class ScreenerConfig:
    oi_z_threshold: float = 2.5
    iv_z_threshold: float = 1.5
    moneyness_cap: float = 0.08


class NseClient:
    def __init__(self) -> None:
        self.headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_fo_symbols(self) -> list[str]:
        data = self._get_json(f"{NSE_BASE}/api/foSecStockWatch?index=stock_opt")
        return sorted({row.get("symbol") for row in data.get("data", []) if row.get("symbol")})

    def get_option_chain(self, symbol: str) -> dict:
        q = urllib.parse.quote(symbol)
        return self._get_json(f"{NSE_BASE}/api/option-chain-equities?symbol={q}")


def _stdev(vals: list[float]) -> float:
    if not vals:
        return 0.0
    mu = sum(vals) / len(vals)
    return math.sqrt(sum((v - mu) ** 2 for v in vals) / len(vals))


def _flatten_chain(payload: dict) -> list[dict]:
    out: list[dict] = []
    for row in payload.get("records", {}).get("data", []):
        strike = row.get("strikePrice")
        for typ in ("CE", "PE"):
            leg = row.get(typ)
            if not leg:
                continue
            out.append(
                {
                    "symbol": leg.get("underlying"),
                    "option_type": typ,
                    "strike": leg.get("strikePrice", strike),
                    "expiry": leg.get("expiryDate"),
                    "spot": leg.get("underlyingValue"),
                    "open_interest": leg.get("openInterest"),
                    "change_in_oi": leg.get("changeinOpenInterest"),
                    "implied_vol": leg.get("impliedVolatility"),
                    "ltp": leg.get("lastPrice"),
                }
            )
    return out


def screen_abnormal_contracts(client: NseClient, symbols: Iterable[str], cfg: ScreenerConfig) -> list[dict]:
    flagged: list[dict] = []
    for symbol in symbols:
        try:
            rows = _flatten_chain(client.get_option_chain(symbol))
        except Exception:
            continue

        valid = []
        for r in rows:
            try:
                spot = float(r["spot"])
                strike = float(r["strike"])
                r["spot"] = spot
                r["strike"] = strike
                r["change_in_oi"] = float(r["change_in_oi"])
                r["implied_vol"] = float(r["implied_vol"])
                r["open_interest"] = float(r["open_interest"])
                r["ltp"] = float(r["ltp"])
                r["moneyness"] = abs(strike - spot) / spot if spot else 999
            except Exception:
                continue
            if r["moneyness"] <= cfg.moneyness_cap:
                valid.append(r)

        for leg in ("CE", "PE"):
            g = [x for x in valid if x["option_type"] == leg]
            if len(g) < 5:
                continue
            oi_vals = [x["change_in_oi"] for x in g]
            iv_vals = [x["implied_vol"] for x in g]
            oi_mean, iv_mean = mean(oi_vals), mean(iv_vals)
            oi_sd, iv_sd = _stdev(oi_vals), _stdev(iv_vals)
            if oi_sd == 0 or iv_sd == 0:
                continue
            for x in g:
                z_oi = (x["change_in_oi"] - oi_mean) / oi_sd
                z_iv = (x["implied_vol"] - iv_mean) / iv_sd
                if z_oi >= cfg.oi_z_threshold and z_iv >= cfg.iv_z_threshold:
                    y = dict(x)
                    y["z_oi"] = z_oi
                    y["z_iv"] = z_iv
                    y["signal"] = "Bullish-Call OI build" if leg == "CE" else "Bearish-Put OI build"
                    flagged.append(y)
    flagged.sort(key=lambda x: (x["z_oi"], x["z_iv"]), reverse=True)
    return flagged
