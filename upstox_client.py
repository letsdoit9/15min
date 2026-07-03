"""
UPSTOX CLIENT
=============
Upstox API se candle data fetch karne ke helper functions.
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

BASE_URL = "https://api.upstox.com/v3"


def _headers(access_token: str = None):
    token = access_token or ACCESS_TOKEN
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }


def get_intraday_candles(instrument_key: str, access_token: str = None, unit: str = "minutes", interval: str = "5") -> pd.DataFrame:
    """
    Aaj (current trading day) ki candles fetch karta hai.
    access_token: agar diya to isse use karega, warna .env wala ACCESS_TOKEN use hoga
                  (Streamlit app session token pass karega, local script .env se lega)
    Returns: DataFrame with columns [timestamp, open, high, low, close, volume, oi]
             sorted purane se naye (ascending time) order me.
    """
    url = f"{BASE_URL}/historical-candle/intraday/{instrument_key}/{unit}/{interval}"
    resp = requests.get(url, headers=_headers(access_token))

    if resp.status_code != 200:
        raise RuntimeError(f"Upstox API error ({instrument_key}): {resp.status_code} - {resp.text}")

    data = resp.json()
    candles = data.get("data", {}).get("candles", [])

    if not candles:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])

    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def get_historical_candles(instrument_key: str, unit: str, interval: str, to_date: str, from_date: str) -> pd.DataFrame:
    """
    Purane din(s) ki candles fetch karta hai (backtesting / dataset banane ke liye).
    Dates format: YYYY-MM-DD
    """
    url = f"{BASE_URL}/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}"
    resp = requests.get(url, headers=_headers())

    if resp.status_code != 200:
        raise RuntimeError(f"Upstox API error ({instrument_key}): {resp.status_code} - {resp.text}")

    data = resp.json()
    candles = data.get("data", {}).get("candles", [])

    if not candles:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])

    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
