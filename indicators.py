"""
INDICATORS
==========
Candle dataframe se technical indicators nikalne ke functions.
Har function pandas Series return karta hai jo df me easily add ho sake.
"""

import pandas as pd
import numpy as np


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price - din ki shuruwat se ab tak"""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
    cumulative_vol = df["volume"].cumsum().replace(0, np.nan)
    return cumulative_tp_vol / cumulative_vol


def calculate_ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    """Exponential Moving Average"""
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Relative Strength Index"""
    delta = df[column].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # shuruwat me data kam hone par neutral 50 rakho


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range - volatility measure"""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period, min_periods=1).mean()


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ek hi call me saare indicators daal deta hai.
    NOTE: Intraday me EMA20/50 aur RSI(14) ke liye kam se kam utni candles honi chahiye,
    warna shuruwati values approximate/unstable hongi - ye normal hai.
    """
    df = df.copy()
    df["vwap"] = calculate_vwap(df)
    df["ema20"] = calculate_ema(df, 20)
    df["ema50"] = calculate_ema(df, 50)
    df["rsi"] = calculate_rsi(df, 14)
    df["atr"] = calculate_atr(df, 14)
    return df
