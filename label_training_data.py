"""
LABEL TRAINING DATA
====================
Ye script `output/screener_log.csv` ki BREAKOUT rows uthata hai aur har ek ke
liye us din ka BAAKI candle data (Upstox historical API se) fetch karke khud
decide karta hai ki trade "successful" rahi ya "fail":

  - Target pehle hit hua  -> actual_result = 1 (success)
  - Stoploss pehle hit hua -> actual_result = 0 (fail)
  - Din khatam ho gaya, kuch hit nahi hua -> actual_result = 0 (EOD, no clean win)

Entry/Stoploss/Target kaise decide hote hain:
  BULLISH breakout: entry = range_high, stoploss = range_low,
                     target = entry + (entry - stoploss) * TARGET_RISK_REWARD_RATIO
  BEARISH breakout: entry = range_low,  stoploss = range_high,
                     target = entry - (stoploss - entry) * TARGET_RISK_REWARD_RATIO

(Ratio config.py me TARGET_RISK_REWARD_RATIO se change kar sakte ho.)

Result `output/training_data.csv` me save hota hai — yehi file future me
ML model (XGBoost etc.) train karne ke kaam aayegi.

IMPORTANT:
  - Sirf PURANE din ki BREAKOUT rows label hoti hain (aaj ka din chhoda jaata hai,
    kyunki din abhi khatam nahi hua - poora data available nahi hai).
  - Script IDEMPOTENT hai - jo symbol+date pehle se training_data.csv me label
    ho chuka hai, use dobara skip kar dega. Isliye ise roz (ya jab bhi chaho)
    dobara chalana safe hai.
  - Isse chalane ke liye bhi taaza access token chahiye (jaisa main.py ke liye
    chahiye hota hai) - pehle `python get_access_token.py` chala lena.

Chalane ka tareeka:  python label_training_data.py
"""

import os
import time
from datetime import datetime
import pandas as pd

import config
from upstox_client import get_historical_candles


def load_screener_log() -> pd.DataFrame:
    if not os.path.isfile(config.LOG_CSV):
        print(f"❌ {config.LOG_CSV} nahi mili. Pehle main.py ya streamlit app chala ke kuch data collect karo.")
        raise SystemExit(1)
    return pd.read_csv(config.LOG_CSV)


def load_existing_training_data() -> pd.DataFrame:
    if os.path.isfile(config.TRAINING_DATA_CSV):
        return pd.read_csv(config.TRAINING_DATA_CSV)
    return pd.DataFrame()


def already_labeled_keys(training_df: pd.DataFrame) -> set:
    if training_df.empty:
        return set()
    return set(zip(training_df["symbol"], training_df["date"].astype(str)))


def _to_naive(ts) -> pd.Timestamp:
    """Timezone hata deta hai taaki comparison me mismatch na aaye."""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts


def get_entry_stop_target(row) -> tuple:
    """Signal ke direction ke hisaab se entry, stoploss, target, risk nikalta hai."""
    range_high = float(row["range_high"])
    range_low = float(row["range_low"])

    if row["signal"] == "BULLISH":
        entry = range_high
        stoploss = range_low
        risk = entry - stoploss
        target = entry + risk * config.TARGET_RISK_REWARD_RATIO
    else:  # BEARISH
        entry = range_low
        stoploss = range_high
        risk = stoploss - entry
        target = entry - risk * config.TARGET_RISK_REWARD_RATIO

    return entry, stoploss, target, risk


def label_row(row) -> dict:
    """
    Ek BREAKOUT row ko label karta hai. Poore din ka historical data fetch
    karke dekhta hai ki target pehle hit hua ya stoploss.
    """
    symbol = row["symbol"]
    trade_date = str(row["date"])
    instrument_key = config.WATCHLIST.get(symbol)

    if not instrument_key:
        return {"actual_result": None, "exit_reason": "SYMBOL_NOT_IN_WATCHLIST"}

    entry, stoploss, target, risk = get_entry_stop_target(row)
    if risk <= 0:
        return {"actual_result": None, "exit_reason": "INVALID_RISK"}

    try:
        df = get_historical_candles(
            instrument_key,
            unit=config.CANDLE_INTERVAL_UNIT,
            interval=config.CANDLE_INTERVAL_VALUE,
            to_date=trade_date,
            from_date=trade_date,
        )
    except Exception as e:
        return {"actual_result": None, "exit_reason": f"FETCH_ERROR: {e}"}

    if df.empty:
        return {"actual_result": None, "exit_reason": "NO_DATA"}

    breakout_time = _to_naive(row["breakout_time"])
    df["timestamp"] = df["timestamp"].apply(_to_naive)

    # Sirf breakout candle ke BAAD ki candles chahiye (aage ka price action)
    after = df[df["timestamp"] > breakout_time].reset_index(drop=True)

    if after.empty:
        return {"actual_result": None, "exit_reason": "NO_CANDLES_AFTER_BREAKOUT"}

    exit_reason = "EOD_NO_HIT"
    exit_price = float(after.iloc[-1]["close"])
    bars_to_exit = len(after)

    for i, candle in after.iterrows():
        if row["signal"] == "BULLISH":
            hit_target = candle["high"] >= target
            hit_stop = candle["low"] <= stoploss
        else:
            hit_target = candle["low"] <= target
            hit_stop = candle["high"] >= stoploss

        if hit_target and hit_stop:
            # Dono ek hi candle me hit ho sakte hain - conservative assumption:
            # stoploss pehle hit maano (worst case, real trading me bhi yehi safe hai)
            exit_reason, exit_price, bars_to_exit = "STOPLOSS_HIT", stoploss, i + 1
            break
        elif hit_target:
            exit_reason, exit_price, bars_to_exit = "TARGET_HIT", target, i + 1
            break
        elif hit_stop:
            exit_reason, exit_price, bars_to_exit = "STOPLOSS_HIT", stoploss, i + 1
            break

    actual_result = 1 if exit_reason == "TARGET_HIT" else 0

    return {
        "entry_price": round(entry, 2),
        "stoploss_price": round(stoploss, 2),
        "target_price": round(target, 2),
        "exit_price": round(float(exit_price), 2),
        "exit_reason": exit_reason,
        "bars_to_exit": bars_to_exit,
        "actual_result": actual_result,
    }


def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    log_df = load_screener_log()
    training_df = load_existing_training_data()
    done_keys = already_labeled_keys(training_df)

    today_str = datetime.now().strftime("%Y-%m-%d")
    breakout_rows = log_df[
        (log_df["status"] == "BREAKOUT") & (log_df["date"].astype(str) < today_str)
    ].copy()

    if breakout_rows.empty:
        print("Koi purani BREAKOUT row nahi mili label karne ke liye.")
        return

    new_rows = []
    skipped = 0

    print(f"🔍 {len(breakout_rows)} BREAKOUT rows mili, {len(done_keys)} pehle se labeled hain.\n")

    for _, row in breakout_rows.iterrows():
        key = (row["symbol"], str(row["date"]))
        if key in done_keys:
            continue

        labeled = label_row(row)
        if labeled.get("actual_result") is None:
            print(f"⚠️  {row['symbol']} ({row['date']}): skip - {labeled.get('exit_reason')}")
            skipped += 1
            time.sleep(0.3)
            continue

        combined = row.to_dict()
        combined.update(labeled)
        new_rows.append(combined)
        print(f"✅ {row['symbol']} ({row['date']}): {labeled['exit_reason']} "
              f"(bars: {labeled['bars_to_exit']}) -> result={labeled['actual_result']}")
        time.sleep(0.3)  # API rate limit se bachne ke liye

    if not new_rows:
        print(f"\nKoi naya row label nahi hua. ({skipped} skip hue - error/data missing.)")
        return

    new_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([training_df, new_df], ignore_index=True)
    combined_df.to_csv(config.TRAINING_DATA_CSV, index=False)

    print(f"\n✅ {len(new_df)} naye rows label ho gaye ({skipped} skip hue).")
    print(f"📊 Total training data ab: {len(combined_df)} rows")
    print(f"💾 Saved: {config.TRAINING_DATA_CSV}")


if __name__ == "__main__":
    main()
