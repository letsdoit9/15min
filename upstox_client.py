"""
UPSTOX CLIENT
=============
Upstox API se candle data fetch karne ke helper functions.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")

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


def get_historical_candles(instrument_key: str, unit: str, interval: str, to_date: str, from_date: str, access_token: str = None) -> pd.DataFrame:
    """
    Purane din(s) ki candles fetch karta hai (backtesting / dataset banane ke liye).
    Dates format: YYYY-MM-DD
    access_token: agar diya to isse use karega, warna .env wala ACCESS_TOKEN use hoga
    """
    url = f"{BASE_URL}/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}"
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


def get_candles(instrument_key: str, access_token: str = None, unit: str = "minutes", interval: str = "5") -> pd.DataFrame:
    """
    SMART WRAPPER - isi ko use karo (get_intraday_candles/get_historical_candles
    directly call karne ki zarurat nahi).

    Pehle intraday API try karta hai (market hours ke liye sahi tareeka).
    Agar wo KHAALI data de - jaise market band hone ke kaafi baad (raat ko),
    jab Upstox ka backend us din ka data abhi 'historical' bucket me process
    kar raha hota hai - to automatically historical API pe fallback ho jaata hai
    (aaj ki hi date use karke).

    Matlab: chahe subah 9:35 pe chalao, dopahar 2 baje, ya raat 8 baje -
    ye khud sahi source se data laane ki koshish karega, tumhe kuch sochna
    nahi padega.

    NOTE: Agar market abhi tak khula hi nahi (jaise raat 2 AM, ya weekend/holiday
    jab us din trading hui hi nahi), to dono API khaali dengi - tab bhi
    empty DataFrame hi milega, kyunki us din candles bani hi nahi.
    """
    df = get_intraday_candles(instrument_key, access_token=access_token, unit=unit, interval=interval)
    if not df.empty:
        return df

    # Intraday khaali aaya - historical API try karo (aaj ki date se)
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    df = get_historical_candles(
        instrument_key,
        unit=unit,
        interval=interval,
        to_date=today_str,
        from_date=today_str,
        access_token=access_token,
    )
    return df
