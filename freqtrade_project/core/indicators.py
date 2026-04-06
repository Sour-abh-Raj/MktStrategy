from __future__ import annotations

from statistics import mean
from typing import Dict, List


def ema(values: List[float], period: int) -> List[float]:
    """Exponential moving average with standard EMA formula."""
    if not values:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def wilder_smooth(values: List[float], period: int) -> List[float]:
    """Wilder's smoothed moving average (used in RSI, ATR, ADX)."""
    if not values or period <= 0:
        return []
    # Seed with the simple average of the first `period` values
    if len(values) < period:
        return [mean(values[:n + 1]) for n in range(len(values))]
    seed = mean(values[:period])
    result: List[float] = [0.0] * (period - 1) + [seed]
    alpha = 1 / period
    for v in values[period:]:
        result.append((1 - alpha) * result[-1] + alpha * v)
    return result


def rsi(values: List[float], period: int = 14) -> List[float]:
    """RSI using Wilder's smoothed method (industry-standard).

    Returns a list of RSI values of the same length as input.
    Positions with insufficient data are filled with 50.0.
    """
    n = len(values)
    if n < period + 1:
        return [50.0] * n

    gains: List[float] = [0.0]
    losses: List[float] = [0.0]
    for i in range(1, n):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))

    rsis = [50.0] * n
    # Seed averages for the first `period` windows
    avg_gain = mean(gains[1: period + 1])
    avg_loss = mean(losses[1: period + 1])
    alpha = 1 / period

    for i in range(period, n):
        if i > period:
            avg_gain = (1 - alpha) * avg_gain + alpha * gains[i]
            avg_loss = (1 - alpha) * avg_loss + alpha * losses[i]
        else:
            avg_gain = mean(gains[1: period + 1])
            avg_loss = mean(losses[1: period + 1])
        rs = avg_gain / avg_loss if avg_loss > 0 else 100.0
        rsis[i] = 100 - (100 / (1 + rs))
    return rsis


def macd_hist(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> List[float]:
    """MACD histogram = (MACD line) - (signal line)."""
    if not values:
        return []
    fast_ema = ema(values, fast)
    slow_ema = ema(values, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    return [m - s for m, s in zip(macd_line, signal_line)]


def bollinger(values: List[float], period: int = 20, std_mult: float = 2.0) -> Dict[str, List[float]]:
    """Bollinger Bands: mid, upper, lower."""
    if len(values) < period:
        return {"mid": values[:], "upper": values[:], "lower": values[:]}
    mid: List[float] = []
    upper: List[float] = []
    lower: List[float] = []
    for i in range(len(values)):
        window = values[max(0, i - period + 1): i + 1]
        m = mean(window)
        var = sum((x - m) ** 2 for x in window) / max(len(window), 1)
        sd = var ** 0.5
        mid.append(m)
        upper.append(m + std_mult * sd)
        lower.append(m - std_mult * sd)
    return {"mid": mid, "upper": upper, "lower": lower}


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """Average True Range using Wilder's smoothed method."""
    if len(closes) < 2:
        return [0.0] * len(closes)
    trs: List[float] = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        trs.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        ))
    smoothed = wilder_smooth(trs, period)
    return smoothed


def adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """Average Directional Index (ADX) — measures trend strength (0-100).

    Returns a list the same length as closes; leading values are 0.0 until
    enough data is available.
    """
    n = len(closes)
    if n < period + 1:
        return [0.0] * n

    plus_dm: List[float] = [0.0]
    minus_dm: List[float] = [0.0]
    tr_list: List[float] = [highs[0] - lows[0]]

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        dn_move = lows[i - 1] - lows[i]
        tr_list.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        ))
        plus_dm.append(up_move if up_move > dn_move and up_move > 0 else 0.0)
        minus_dm.append(dn_move if dn_move > up_move and dn_move > 0 else 0.0)

    smooth_tr = wilder_smooth(tr_list, period)
    smooth_pdm = wilder_smooth(plus_dm, period)
    smooth_mdm = wilder_smooth(minus_dm, period)

    dx_list: List[float] = []
    for i in range(n):
        atr_val = smooth_tr[i]
        if atr_val < 1e-9:
            dx_list.append(0.0)
        else:
            pdi = 100 * smooth_pdm[i] / atr_val
            mdi = 100 * smooth_mdm[i] / atr_val
            denom = pdi + mdi
            dx_list.append(100 * abs(pdi - mdi) / denom if denom > 0 else 0.0)

    adx_smooth = wilder_smooth(dx_list, period)
    return [round(v, 4) for v in adx_smooth]
