from __future__ import annotations

from statistics import mean, pstdev
from typing import Dict, List

from freqtrade_project.core.indicators import adx as compute_adx
from freqtrade_project.core.indicators import ema, macd_hist, rsi
from freqtrade_project.data_layer.data_collector.binance_collector import Candle


class FeatureEngineeringEngine:
    """Build a flat indicator dict from a list of Candle objects.

    All keys required by RegimeClassifier are populated:
        close, ma_fast, ma_slow, ma_slope,
        rsi, macd_hist, adx,
        realized_volatility, momentum_score,
        volume_ratio, atr,
        price_change_5m, price_change_15m
    """

    def build(self, candles: List[Candle], lookback: int = 50) -> Dict[str, float]:
        """Return indicator dict from the most-recent `lookback` candles.

        Requires at least 30 candles for meaningful indicators; returns {}
        for shorter series.
        """
        min_required = max(lookback, 30)
        if len(candles) < min_required:
            if len(candles) >= 3:
                # Return a minimal feature set so pipeline doesn't hard-fail
                return self._minimal(candles)
            return {}

        window = candles[-lookback:]
        closes = [c.close for c in window]
        highs = [c.high for c in window]
        lows = [c.low for c in window]
        volumes = [c.volume for c in window]

        # --- Price / MA features ---
        ma_fast = mean(closes[-5:])
        ma_slow = mean(closes)
        ma_slope = (ma_fast - ma_slow) / max(ma_slow, 1e-9)

        # --- Returns ---
        returns = [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]

        # --- Volatility ---
        realized_vol = pstdev(returns) if len(returns) > 1 else 0.0

        # --- Momentum (full-window return) ---
        momentum_score = (closes[-1] / closes[0]) - 1 if closes[0] > 0 else 0.0

        # --- Volume ---
        vol_avg = mean(volumes)
        volume_ratio = volumes[-1] / max(vol_avg, 1e-9)

        # --- RSI (Wilder) ---
        rsi_series = rsi(closes, period=14)
        rsi_val = rsi_series[-1]

        # --- MACD histogram ---
        if len(closes) >= 35:
            macd_series = macd_hist(closes, fast=12, slow=26, signal=9)
            macd_val = macd_series[-1]
        else:
            # Fast EMAs only
            fast_ema = ema(closes, 12)
            slow_ema = ema(closes, 26)
            macd_val = fast_ema[-1] - slow_ema[-1]

        # --- ADX ---
        adx_series = compute_adx(highs, lows, closes, period=14)
        adx_val = adx_series[-1]

        # --- ATR ---
        from freqtrade_project.core.indicators import atr as compute_atr

        atr_series = compute_atr(highs, lows, closes, period=14)
        atr_val = atr_series[-1]

        # --- Short-term price changes ---
        price_change_5m = returns[-1] if returns else 0.0
        price_change_15m = sum(returns[-3:]) if len(returns) >= 3 else price_change_5m

        return {
            "close": closes[-1],
            "ma_fast": ma_fast,
            "ma_slow": ma_slow,
            "ma_slope": ma_slope,
            "rsi": rsi_val,
            "macd_hist": macd_val,
            "adx": adx_val,
            "realized_volatility": realized_vol,
            "momentum_score": momentum_score,
            "volume_ratio": volume_ratio,
            "atr": atr_val,
            "price_change_5m": price_change_5m,
            "price_change_15m": price_change_15m,
        }

    def _minimal(self, candles: List[Candle]) -> Dict[str, float]:
        """Return a neutral feature set for very short candle series."""
        closes = [c.close for c in candles]
        return {
            "close": closes[-1],
            "ma_fast": closes[-1],
            "ma_slow": closes[-1],
            "ma_slope": 0.0,
            "rsi": 50.0,
            "macd_hist": 0.0,
            "adx": 0.0,
            "realized_volatility": 0.02,
            "momentum_score": 0.0,
            "volume_ratio": 1.0,
            "atr": 0.0,
            "price_change_5m": 0.0,
            "price_change_15m": 0.0,
        }
