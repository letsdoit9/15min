"""
SCREENER
========
Core logic: opening range nikalna, breakout detect karna, aur rule-based
confidence score dena (abhi ML nahi hai - pehle isse data collect hoga).
"""

import pandas as pd
from indicators import add_all_indicators
import config


def get_opening_range(df: pd.DataFrame):
    """
    Pehli N candles (config.OPENING_RANGE_CANDLES) ka high/low nikalta hai.
    Returns: (range_high, range_low, range_df) ya (None, None, None) agar data kam hai
    """
    n = config.OPENING_RANGE_CANDLES
    if len(df) < n:
        return None, None, None

    range_df = df.iloc[:n]
    range_high = range_df["high"].max()
    range_low = range_df["low"].min()
    return range_high, range_low, range_df


def evaluate_stock(symbol: str, df: pd.DataFrame) -> dict:
    """
    Ek stock ke liye poora evaluation karta hai.
    df: aaj ki 5-min candles (ascending time order me)

    Returns dict jisme signal, confidence, aur saare raw features hain
    (ye dict hi future me CSV row / ML training row banega).
    """
    result = {
        "symbol": symbol,
        "status": None,       # NOT_READY / RANGE_TOO_SMALL / RANGE_TOO_WIDE / NO_BREAKOUT / BREAKOUT
        "signal": None,       # BULLISH / BEARISH / NONE
        "confidence": 0,
        "volume_score": None,
        "body_score": None,
        "trend_score": None,
        "rsi_score": None,
        "label": None,
        "range_high": None,
        "range_low": None,
        "range_pct": None,
        "breakout_candle_volume": None,
        "volume_ratio": None,
        "body_pct": None,
        "upper_wick_pct": None,
        "lower_wick_pct": None,
        "close_above_vwap": None,
        "ema20_above_ema50": None,
        "rsi": None,
        "atr": None,
        "breakout_time": None,
    }

    check_idx = config.BREAKOUT_CHECK_CANDLE_INDEX  # 4th candle = index 3

    if len(df) <= check_idx:
        result["status"] = "NOT_READY"   # abhi 9:35 nahi hui / itni candles nahi aayi
        return result

    range_high, range_low, range_df = get_opening_range(df)
    if range_high is None:
        result["status"] = "NOT_READY"
        return result

    df = add_all_indicators(df)

    range_size = range_high - range_low
    ref_price = range_df["close"].iloc[-1]
    range_pct = (range_size / ref_price) * 100 if ref_price else 0

    result["range_high"] = round(range_high, 2)
    result["range_low"] = round(range_low, 2)
    result["range_pct"] = round(range_pct, 2)

    if range_pct < config.MIN_RANGE_PERCENT:
        result["status"] = "RANGE_TOO_SMALL"
        return result
    if range_pct > config.MAX_RANGE_PERCENT:
        result["status"] = "RANGE_TOO_WIDE"
        return result

    breakout_candle = df.iloc[check_idx]
    avg_range_volume = range_df["volume"].mean()

    body = abs(breakout_candle["close"] - breakout_candle["open"])
    candle_range = breakout_candle["high"] - breakout_candle["low"]
    body_pct = (body / candle_range * 100) if candle_range else 0

    upper_wick = breakout_candle["high"] - max(breakout_candle["open"], breakout_candle["close"])
    lower_wick = min(breakout_candle["open"], breakout_candle["close"]) - breakout_candle["low"]
    upper_wick_pct = (upper_wick / candle_range * 100) if candle_range else 0
    lower_wick_pct = (lower_wick / candle_range * 100) if candle_range else 0

    volume_ratio = (breakout_candle["volume"] / avg_range_volume) if avg_range_volume else 0

    result.update({
        "breakout_candle_volume": int(breakout_candle["volume"]),
        "volume_ratio": round(volume_ratio, 2),
        "body_pct": round(body_pct, 1),
        "upper_wick_pct": round(upper_wick_pct, 1),
        "lower_wick_pct": round(lower_wick_pct, 1),
        "close_above_vwap": bool(breakout_candle["close"] > breakout_candle["vwap"]),
        "ema20_above_ema50": bool(breakout_candle["ema20"] > breakout_candle["ema50"]),
        "rsi": round(breakout_candle["rsi"], 1),
        "atr": round(breakout_candle["atr"], 2),
        "breakout_time": str(breakout_candle["timestamp"]),
    })

    # Direction decide karo
    direction = None
    if breakout_candle["close"] > range_high:
        direction = "BULLISH"
    elif breakout_candle["close"] < range_low:
        direction = "BEARISH"

    if direction is None:
        result["status"] = "NO_BREAKOUT"
        result["signal"] = "NONE"
        return result

    result["status"] = "BREAKOUT"
    result["signal"] = direction

    # ---- Rule-based WEIGHTED CONTINUOUS confidence score (0-100) ----
    # Hard thresholds ki jagah proportional/continuous scoring - realistic hai
    # kyunki market me "1.29x volume" aur "1.30x volume" me utna fark nahi hota
    # jitna binary scoring dikhata tha.

    # 1. Volume Score (30 pts) - proportional, koi hard cutoff nahi
    volume_score = min(30, (volume_ratio / config.MIN_VOLUME_RATIO) * 30)

    # 2. Candle Strength Score (25 pts) - body dominance (0.0 to 1.0 ka ratio)
    body_ratio = body / candle_range if candle_range else 0
    body_score = body_ratio * 25

    # 3. Trend Score (25 pts) - EMA aur VWAP alignment ko smooth score me convert
    # ASSUMPTION: price-based farak ko % me normalize kiya hai (stock-price-independent
    # banane ke liye), aur +/-1% ke range ko 0-25 scale pe map kiya hai.
    # Agar ye range zyada/kam sensitive lage to config.py me TREND_NORMALIZE_RANGE_PCT badal dena.
    close_price = breakout_candle["close"]
    ema_diff_pct = ((breakout_candle["ema20"] - breakout_candle["ema50"]) / close_price * 100) if close_price else 0
    vwap_diff_pct = ((close_price - breakout_candle["vwap"]) / close_price * 100) if close_price else 0
    trend_raw = ema_diff_pct + vwap_diff_pct  # positive = bullish alignment

    if direction == "BEARISH":
        trend_raw = -trend_raw  # bearish breakout ke liye "downward alignment" hi achha signal hai

    trend_range = config.TREND_NORMALIZE_RANGE_PCT
    trend_raw_clamped = max(-trend_range, min(trend_range, trend_raw))
    trend_score = ((trend_raw_clamped + trend_range) / (2 * trend_range)) * 25

    # 4. RSI Score (20 pts) - continuous momentum scaling (binary threshold nahi)
    # Bullish: RSI 40->0, RSI 60->20 (linear). Bearish: mirror - RSI 60->0, RSI 40->20
    rsi_val = result["rsi"]
    if direction == "BULLISH":
        rsi_score = 20 * (rsi_val - 40) / 20
    else:
        rsi_score = 20 * (60 - rsi_val) / 20
    rsi_score = max(0, min(20, rsi_score))

    total_score = volume_score + body_score + trend_score + rsi_score

    result["volume_score"] = round(volume_score, 1)
    result["body_score"] = round(body_score, 1)
    result["trend_score"] = round(trend_score, 1)
    result["rsi_score"] = round(rsi_score, 1)
    result["confidence"] = round(total_score, 1)

    # Label bucket (jaisa specify kiya tha)
    if total_score >= 80:
        result["label"] = "Strong Breakout"
    elif total_score >= 60:
        result["label"] = "Valid Setup"
    else:
        result["label"] = "Weak / Avoid"

    return result
