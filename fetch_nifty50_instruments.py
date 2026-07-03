"""
FETCH NIFTY50 INSTRUMENT KEYS
==============================
Upstox ki official, daily-updated instrument master file se Nifty50 stocks
ke sahi instrument_key nikalta hai — hath se ISIN likhne se better hai
(galti hone ka chance zero, kyunki ye seedha Upstox ki apni file se aata hai).

Chalane ka tareeka:  python fetch_nifty50_instruments.py

Output: config_watchlist_nifty50.txt banega, uska content copy karke
config.py ke WATCHLIST me paste kar dena.
"""

import gzip
import json
import requests

INSTRUMENT_MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"

# Nifty50 trading symbols (as on NSE, July 2026 composition)
# Agar koi symbol NSE pe recently change hua ho, ye script bata dega ki wo nahi mila
NIFTY50_SYMBOLS = [
    "RELIANCE", "HDFCBANK", "BHARTIARTL", "ICICIBANK", "SBIN",
    "TCS", "BAJFINANCE", "LT", "HINDUNILVR", "MARUTI",
    "SUNPHARMA", "ADANIPORTS", "AXISBANK", "INFY", "ADANIENT",
    "TITAN", "KOTAKBANK", "M&M", "ITC", "NTPC",
    "ULTRACEMCO", "BEL", "JSWSTEEL", "BAJAJFINSV", "ONGC",
    "HCLTECH", "BAJAJ-AUTO", "COALINDIA", "ETERNAL", "POWERGRID",
    "ASIANPAINT", "SHRIRAMFIN", "TATASTEEL", "GRASIM", "HINDALCO",
    "INDIGO", "EICHERMOT", "SBILIFE", "TRENT", "WIPRO",
    "JIOFIN", "TECHM", "APOLLOHOSP", "HDFCLIFE", "CIPLA",
    "DRREDDY", "TATACONSUM", "HEROMOTOCO", "DIVISLAB", "TATAMOTORS",
]


def fetch_instrument_master():
    print("Upstox instrument master download ho raha hai (thoda time lagega)...")
    resp = requests.get(INSTRUMENT_MASTER_URL, timeout=60)
    resp.raise_for_status()
    data = json.loads(gzip.decompress(resp.content))
    print(f"✅ {len(data)} instruments mile.")
    return data


def find_nifty50_keys(instruments):
    found = {}
    for inst in instruments:
        if inst.get("segment") != "NSE_EQ":
            continue
        symbol = inst.get("trading_symbol")
        if symbol in NIFTY50_SYMBOLS and symbol not in found:
            found[symbol] = inst.get("instrument_key")
    return found


if __name__ == "__main__":
    instruments = fetch_instrument_master()
    found = find_nifty50_keys(instruments)

    missing = [s for s in NIFTY50_SYMBOLS if s not in found]

    with open("config_watchlist_nifty50.txt", "w") as f:
        f.write("WATCHLIST = {\n")
        for symbol, key in found.items():
            f.write(f'    "{symbol}": "{key}",\n')
        f.write("}\n")

    print(f"\n✅ {len(found)}/{len(NIFTY50_SYMBOLS)} stocks mile.")
    print("Result 'config_watchlist_nifty50.txt' me save ho gaya.")
    print("Iska content copy karke config.py ke WATCHLIST me paste kar do.\n")

    if missing:
        print("⚠️ Ye symbols nahi mile (shayad NSE pe naam/ticker badla hai, manually check karo):")
        for s in missing:
            print(f"   - {s}")
