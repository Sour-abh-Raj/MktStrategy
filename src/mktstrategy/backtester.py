from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median


@dataclass
class BacktestConfig:
    z_oi_threshold: float = 2.5
    z_iv_threshold: float = 1.5
    lookback: int = 20
    max_moneyness: float = 0.08
    min_dte: int = 2
    max_dte: int = 45
    stop_loss: float = 0.25
    take_profit: float = 0.75
    max_hold_days: int = 5


def _rolling_z(values: list[float], lookback: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i, v in enumerate(values):
        start = max(0, i - lookback + 1)
        window = values[start : i + 1]
        if len(window) < 5:
            continue
        mu = sum(window) / len(window)
        var = sum((x - mu) ** 2 for x in window) / len(window)
        sd = math.sqrt(var)
        if sd == 0:
            continue
        out[i] = (v - mu) / sd
    return out


def prepare_signals(rows: list[dict], cfg: BacktestConfig) -> list[dict]:
    filt: list[dict] = []
    for r in rows:
        if r.get("INSTRUMENT") not in {"OPTSTK", "OPTIDX"}:
            continue
        dte = (r["EXPIRY_DT"] - r["TIMESTAMP"]).days
        if not (cfg.min_dte <= dte <= cfg.max_dte):
            continue
        m = abs(r["STRIKE_PR"] - r["UNDERLYING"]) / r["UNDERLYING"] if r["UNDERLYING"] else 999
        if m > cfg.max_moneyness:
            continue
        x = dict(r)
        x["DTE"] = dte
        x["MONEYNESS"] = m
        filt.append(x)

    groups: dict[tuple, list[dict]] = {}
    for r in filt:
        k = (r["SYMBOL"], r["OPTION_TYP"], r["STRIKE_PR"])
        groups.setdefault(k, []).append(r)

    out: list[dict] = []
    for _, g in groups.items():
        g.sort(key=lambda x: x["TIMESTAMP"])
        oi = [float(x["CHG_IN_OI"]) for x in g]
        iv = [float(x["IMP_VOLT"]) for x in g]
        zoi = _rolling_z(oi, cfg.lookback)
        ziv = _rolling_z(iv, cfg.lookback)
        for i, r in enumerate(g):
            r["Z_OI"] = zoi[i]
            r["Z_IV"] = ziv[i]
            r["SIGNAL"] = (zoi[i] is not None and ziv[i] is not None and zoi[i] >= cfg.z_oi_threshold and ziv[i] >= cfg.z_iv_threshold)
            out.append(r)
    return out


def run_backtest(signals: list[dict], cfg: BacktestConfig) -> tuple[list[dict], dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in signals:
        k = (r["SYMBOL"], r["OPTION_TYP"], r["STRIKE_PR"], r["EXPIRY_DT"])
        groups.setdefault(k, []).append(r)

    trades: list[dict] = []
    for _, g in groups.items():
        g.sort(key=lambda x: x["TIMESTAMP"])
        for i, r in enumerate(g):
            if not r.get("SIGNAL"):
                continue
            entry = float(r["CLOSE"])
            if entry <= 0:
                continue
            end = min(len(g) - 1, i + cfg.max_hold_days)
            exit_i = end
            outcome = "timeout"
            for j in range(i + 1, end + 1):
                ret = float(g[j]["CLOSE"]) / entry - 1
                if ret <= -cfg.stop_loss:
                    exit_i = j
                    outcome = "stop"
                    break
                if ret >= cfg.take_profit:
                    exit_i = j
                    outcome = "target"
                    break

            pnl = float(g[exit_i]["CLOSE"]) / entry - 1
            trades.append(
                {
                    "symbol": r["SYMBOL"],
                    "option_type": r["OPTION_TYP"],
                    "strike": r["STRIKE_PR"],
                    "entry_date": r["TIMESTAMP"].isoformat(),
                    "exit_date": g[exit_i]["TIMESTAMP"].isoformat(),
                    "entry_price": entry,
                    "exit_price": float(g[exit_i]["CLOSE"]),
                    "z_oi": r.get("Z_OI"),
                    "z_iv": r.get("Z_IV"),
                    "outcome": outcome,
                    "return": pnl,
                }
            )

    if not trades:
        return trades, {"trades": 0}

    returns = [x["return"] for x in trades]
    stats = {
        "trades": len(trades),
        "win_rate": sum(1 for r in returns if r > 0) / len(returns),
        "avg_return": mean(returns),
        "median_return": median(returns),
        "total_return_simple": sum(returns),
        "target_hits": sum(1 for t in trades if t["outcome"] == "target"),
        "stop_hits": sum(1 for t in trades if t["outcome"] == "stop"),
    }
    return trades, stats
