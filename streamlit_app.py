"""
STREAMLIT APP
=============
Ye woh file hai jo GitHub + Streamlit Cloud pe deploy hogi.
Isse koi bhi browser se access kar sakta hai, laptop me kuch install nahi karna.

Setup instructions STREAMLIT_DEPLOY.md file me hai - wahi follow karo.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import config
from upstox_client import get_candles, get_historical_candles
from screener import evaluate_stock

st.set_page_config(page_title="ORB Screener", page_icon="📊", layout="wide")
st.title("📊 Opening Range Breakout Screener")
st.caption("Rule-based screener — pehli 3 candles ka range, 4th candle pe breakout check")


# ---------------------------------------------------------
# Access Token: pehle Streamlit "Secrets" se try karo, warna sidebar me manually paste karo
# ---------------------------------------------------------
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default


secret_access_token = get_secret("UPSTOX_ACCESS_TOKEN")

if "access_token" not in st.session_state:
    st.session_state.access_token = secret_access_token or None

with st.sidebar:
    st.header("🔑 Upstox Access Token")
    if secret_access_token:
        st.success("Access Token: secrets se loaded ✅")
    else:
        st.caption(
            "Apne computer par `python get_access_token.py` chalao, "
            "wahan se mila access token neeche (Step 1) me paste karo."
        )

    st.divider()
    if st.session_state.get("access_token"):
        if st.button("🔓 Logout"):
            st.session_state.access_token = None
            st.rerun()


# ---------------------------------------------------------
# Access token daalo - koi OAuth login flow nahi, seedha token paste karo
# ---------------------------------------------------------
st.subheader("Step 1: Access Token Daalo (roz karna hai — token daily expire hota hai)")

if st.session_state.access_token:
    st.success("✅ Access token set hai — is session ke liye active hai.")
else:
    token_input = st.text_input(
        "Apna Upstox Access Token yaha paste karo",
        type="password",
        help="Ye token apne computer par `python get_access_token.py` chalake milta hai "
             "(ya isi ka output .env me se copy karo).",
    )
    if token_input:
        st.session_state.access_token = token_input.strip()
        st.rerun()

st.divider()


# ---------------------------------------------------------
# Watchlist editor
# ---------------------------------------------------------
st.subheader("Step 2: Watchlist")
default_watchlist = "\n".join(f"{k}:{v}" for k, v in config.WATCHLIST.items())
watchlist_text = st.text_area(
    "Format: SYMBOL:instrument_key (ek line me ek stock)",
    value=default_watchlist,
    height=150,
)
watchlist = {}
for line in watchlist_text.strip().splitlines():
    if ":" in line:
        sym, key = line.split(":", 1)
        watchlist[sym.strip()] = key.strip()

st.divider()


# ---------------------------------------------------------
# Run screener
# ---------------------------------------------------------
st.subheader("Step 3: Screener Chalao")
st.caption("9:35 AM ke baad chalao — jab 4th candle (9:30-9:35) complete ho chuki ho")

test_mode = st.checkbox(
    "🧪 Test Mode — purani date se test karo (market band hone par bhi try karne ke liye)"
)
test_date = None
if test_mode:
    test_date = st.date_input(
        "Kis purani trading date ka data mangwana hai?",
        help="2-3 din purani koi normal trading day (Mon-Fri) ki date daalo, "
             "taaki Upstox ka data poora process ho chuka ho.",
    )
    st.caption("⚠️ Ye sirf pipeline test karne ke liye hai — live signal nahi hoga, "
               "purane din ka result dikhega.")

if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame()

run_disabled = not st.session_state.access_token or not watchlist
if st.button("🔍 Run Screener Now", disabled=run_disabled, type="primary"):
    rows = []
    progress = st.progress(0, text="Screening chal raha hai...")
    for i, (symbol, instrument_key) in enumerate(watchlist.items()):
        try:
            if test_mode and test_date:
                date_str = test_date.strftime("%Y-%m-%d")
                df = get_historical_candles(
                    instrument_key,
                    unit=config.CANDLE_INTERVAL_UNIT,
                    interval=config.CANDLE_INTERVAL_VALUE,
                    to_date=date_str,
                    from_date=date_str,
                    access_token=st.session_state.access_token,
                )
            else:
                df = get_candles(instrument_key, access_token=st.session_state.access_token)
            result = evaluate_stock(symbol, df)
        except Exception as e:
            result = {"symbol": symbol, "status": "ERROR", "signal": None, "confidence": 0, "error": str(e)}
        rows.append(result)
        progress.progress((i + 1) / len(watchlist), text=f"{symbol} done")
    progress.empty()

    result_df = pd.DataFrame(rows)
    result_df["date"] = test_date.strftime("%Y-%m-%d") if (test_mode and test_date) else datetime.now().strftime("%Y-%m-%d")
    result_df["logged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.session_state.log_df = pd.concat([st.session_state.log_df, result_df], ignore_index=True)

    breakouts = result_df[result_df["status"] == "BREAKOUT"].sort_values("confidence", ascending=False)
    if not breakouts.empty:
        st.success(f"📈 {len(breakouts)} breakout(s) mile!")
        display_cols = ["symbol", "signal", "confidence", "label", "volume_score", "body_score",
                         "trend_score", "rsi_score", "range_low", "range_high", "volume_ratio", "body_pct"]
        display_cols = [c for c in display_cols if c in breakouts.columns]
        st.dataframe(breakouts[display_cols], use_container_width=True)
    else:
        st.info("Abhi tak koi breakout nahi mila.")

    with st.expander("Saare stocks ka poora status dekho"):
        st.dataframe(result_df, use_container_width=True)

if run_disabled and not st.session_state.access_token:
    st.info("⬆️ Screener chalane ke liye pehle login karo.")


# ---------------------------------------------------------
# Download CSV - user isko roz manually save karega, yehi future ML data hai
# ---------------------------------------------------------
if not st.session_state.log_df.empty:
    st.divider()
    st.subheader("Step 4: Data Save Karo")
    st.caption(
        "⚠️ Streamlit Cloud pe data persist NAHI hota (app restart hone par sab data khatam ho jaata hai). "
        "Isliye har baar screener chalane ke baad ye CSV download karke apne laptop me ek folder me save karte jaana. "
        "Ye files hi future me ML model training ke liye use hongi."
    )
    csv = st.session_state.log_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV (is session ka data)",
        data=csv,
        file_name=f"screener_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
    st.dataframe(st.session_state.log_df, use_container_width=True)
