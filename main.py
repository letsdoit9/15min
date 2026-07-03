"""
MAIN
====
Isse roz market open hone ke baad (9:35 AM ke aas paas) chalao.
Chalane ka tareeka:  python main.py

Ye poore watchlist ko screen karega aur:
  1. Terminal me result dikhayega
  2. output/screener_log.csv me row append karega (future ML training data)
"""

import os
import time
from datetime import datetime
import pandas as pd

import config
from upstox_client import get_candles
from screener import evaluate_stock


def run_screener():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    results = []

    for symbol, instrument_key in config.WATCHLIST.items():
        try:
            df = get_candles(
                instrument_key,
                unit=config.CANDLE_INTERVAL_UNIT,
                interval=config.CANDLE_INTERVAL_VALUE,
            )
            result = evaluate_stock(symbol, df)
        except Exception as e:
            result = {"symbol": symbol, "status": "ERROR", "signal": None, "confidence": 0, "error": str(e)}

        results.append(result)
        time.sleep(0.3)  # API rate limit se bachne ke liye chota sa gap

    return pd.DataFrame(results)


def print_results(df: pd.DataFrame):
    breakouts = df[df["status"] == "BREAKOUT"].sort_values("confidence", ascending=False)
    others = df[df["status"] != "BREAKOUT"]

    print("\n" + "=" * 60)
    print(f"  OPENING RANGE BREAKOUT SCREENER  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if breakouts.empty:
        print("\nAbhi tak koi breakout nahi mila.\n")
    else:
        print("\n📈 BREAKOUTS FOUND:\n")
        for _, row in breakouts.iterrows():
            emoji = "🟢" if row["signal"] == "BULLISH" else "🔴"
            print(f"{emoji} {row['symbol']:12s}  {row['signal']:8s}  "
                  f"Score: {row['confidence']:5.1f}  [{row['label']}]   "
                  f"Range: {row['range_low']}-{row['range_high']}  "
                  f"Vol Ratio: {row['volume_ratio']}x  Body%: {row['body_pct']}")

    print("\n--- Baaki stocks ---")
    for _, row in others.iterrows():
        print(f"  {row['symbol']:12s}  {row['status']}")
    print()


def save_log(df: pd.DataFrame):
    df = df.copy()
    df["date"] = datetime.now().strftime("%Y-%m-%d")
    df["logged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_exists = os.path.isfile(config.LOG_CSV)
    df.to_csv(config.LOG_CSV, mode="a", header=not file_exists, index=False)
    print(f"✅ Results {config.LOG_CSV} me save ho gaye (future ML training ke liye).")


if __name__ == "__main__":
    result_df = run_screener()
    print_results(result_df)
    save_log(result_df)
