"""
TEST SCREENER (PURANI DATE SE)
================================
Ye script market khulne ka wait kiye bina, kisi bhi PURANE trading din
(jo already poora complete ho chuka ho) ka data mangwa ke screener test
karta hai. Isse pipeline check kar sakte ho ki sab sahi chal raha hai,
bina 9:35 AM ka intezaar kiye.

Chalane ka tareeka:
    python test_past_date.py 2026-07-02

Date na do to default kal (ya pichla trading din) use hoga - lekin sabse
bharosemand tareeka hai khud koi pakki purani date (jaise 2-3 din pehle
ka) daal ke chalana, taaki Upstox ka data-processing-lag wala issue na aaye.

NOTE: Agar tumne dee gayi date ko market band tha (weekend/holiday), to
result khaali/NOT_READY aayega - kisi normal trading day (Mon-Fri) ki
date use karo.
"""

import sys
import pandas as pd

import config
from upstox_client import get_historical_candles
from screener import evaluate_stock


def run_test(test_date: str):
    print(f"\n🔍 Testing with date: {test_date}\n")
    results = []

    for symbol, instrument_key in config.WATCHLIST.items():
        try:
            df = get_historical_candles(
                instrument_key,
                unit=config.CANDLE_INTERVAL_UNIT,
                interval=config.CANDLE_INTERVAL_VALUE,
                to_date=test_date,
                from_date=test_date,
            )
            if df.empty:
                result = {"symbol": symbol, "status": "NO_DATA", "signal": None, "confidence": 0}
            else:
                result = evaluate_stock(symbol, df)
        except Exception as e:
            result = {"symbol": symbol, "status": "ERROR", "signal": None, "confidence": 0, "error": str(e)}

        results.append(result)

    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    print(f"\n✅ Test complete — {len(df_results)} stocks evaluate hue.\n")

    if (df_results["status"] == "NO_DATA").all():
        print("⚠️  Sabka status NO_DATA hai — ho sakta hai ye date market-holiday/weekend ho,")
        print("   ya Upstox ne abhi tak is din ka data historical bucket me process na kiya ho.")
        print("   2-3 din purani koi date try karo.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_past_date.py YYYY-MM-DD")
        print("Example: python test_past_date.py 2026-07-02")
        sys.exit(1)

    run_test(sys.argv[1])
