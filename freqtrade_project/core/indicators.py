from __future__ import annotations

from statistics import mean
from typing import Dict, List


def ema(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def rsi(values: List[float], period: int = 14) -> List[float]:
    if len(values) < period + 1:
        return [50.0] * len(values)
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    rsis = [50.0] * len(values)
    for i in range(period, len(values)):
        avg_gain = mean(gains[i - period + 1 : i + 1])
        avg_loss = mean(losses[i - period + 1 : i + 1])
        if avg_loss == 0:
            rs = 100.0
        else:
            rs = avg_gain / avg_loss
        rsis[i] = 100 - (100 / (1 + rs))
    return rsis


def macd_hist(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> List[float]:
    if not values:
        return []
    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    return [m - s for m, s in zip(macd_line, signal_line)]


def bollinger(values: List[float], period: int = 20, std_mult: float = 2.0) -> Dict[str, List[float]]:
    if len(values) < period:
        return {"mid": values[:], "upper": values[:], "lower": values[:]}
    mid: List[float] = []
    upper: List[float] = []
    lower: List[float] = []
    for i in range(len(values)):
        window = values[max(0, i - period + 1) : i + 1]
        m = mean(window)
        var = sum((x - m) ** 2 for x in window) / max(len(window), 1)
        sd = var ** 0.5
        mid.append(m)
        upper.append(m + std_mult * sd)
        lower.append(m - std_mult * sd)
    return {"mid": mid, "upper": upper, "lower": lower}


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    if len(closes) < 2:
        return [0.0] * len(closes)
    trs = [0.0]
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    out: List[float] = []
    for i in range(len(trs)):
        window = trs[max(0, i - period + 1) : i + 1]
        out.append(mean(window))
    return out
