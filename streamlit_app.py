"""
STREAMLIT APP
=============
Ye woh file hai jo GitHub + Streamlit Cloud pe deploy hogi.
Isse koi bhi browser se access kar sakta hai, laptop me kuch install nahi karna.

Setup instructions STREAMLIT_DEPLOY.md file me hai - wahi follow karo.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

import config
from upstox_client import get_intraday_candles
from screener import evaluate_stock

st.set_page_config(page_title="ORB Screener", page_icon="📊", layout="wide")
st.title("📊 Opening Range Breakout Screener")
st.caption("Rule-based screener — pehli 3 candles ka range, 4th candle pe breakout check")


# ---------------------------------------------------------
# Credentials: pehle Streamlit "Secrets" se try karo, warna sidebar me manually daalo
# ---------------------------------------------------------
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default


api_key = get_secret("UPSTOX_API_KEY")
api_secret = get_secret("UPSTOX_API_SECRET")
redirect_uri = get_secret("UPSTOX_REDIRECT_URI")

with st.sidebar:
    st.header("⚙️ Upstox Credentials")
    if not api_key:
        api_key = st.text_input("API Key", type="password")
    else:
        st.success("API Key: secrets se loaded ✅")
    if not api_secret:
        api_secret = st.text_input("API Secret", type="password")
    else:
        st.success("API Secret: secrets se loaded ✅")
    if not redirect_uri:
        redirect_uri = st.text_input(
            "Redirect URI",
            help="Yehi is app ka URL hona chahiye, Upstox app settings me bhi same daalna",
        )
    else:
        st.success("Redirect URI: secrets se loaded ✅")

    st.divider()
    if st.session_state.get("access_token"):
        if st.button("🔓 Logout"):
            st.session_state.access_token = None
            st.rerun()


# ---------------------------------------------------------
# Login flow (OAuth) - Upstox login ke baad is hi app pe ?code=XXXX ke saath wapas aata hai
# ---------------------------------------------------------
if "access_token" not in st.session_state:
    st.session_state.access_token = None

query_params = st.query_params
auth_code = query_params.get("code")

st.subheader("Step 1: Login (roz karna hai — token daily expire hota hai)")

if st.session_state.access_token:
    st.success("✅ Logged in — is session ke liye access token active hai.")
elif auth_code and api_key and api_secret and redirect_uri:
    token_url = "https://api.upstox.com/v2/login/authorization/token"
    payload = {
        "code": auth_code,
        "client_id": api_key,
        "client_secret": api_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    headers = {"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(token_url, data=payload, headers=headers)

    if resp.status_code == 200:
        st.session_state.access_token = resp.json()["access_token"]
        st.query_params.clear()
        st.success("✅ Login successful!")
        st.rerun()
    else:
        st.error(f"Token exchange fail hua: {resp.status_code} - {resp.text}")
elif api_key and redirect_uri:
    login_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}"
    )
    st.link_button("👉 Upstox se Login Karo", login_url)
    st.caption("Login ke baad automatically isi page pe wapas aa jaoge.")
else:
    st.warning("⚠️ Pehle sidebar me API Key, Secret, aur Redirect URI bharo.")

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

if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame()

run_disabled = not st.session_state.access_token or not watchlist
if st.button("🔍 Run Screener Now", disabled=run_disabled, type="primary"):
    rows = []
    progress = st.progress(0, text="Screening chal raha hai...")
    for i, (symbol, instrument_key) in enumerate(watchlist.items()):
        try:
            df = get_intraday_candles(instrument_key, access_token=st.session_state.access_token)
            result = evaluate_stock(symbol, df)
        except Exception as e:
            result = {"symbol": symbol, "status": "ERROR", "signal": None, "confidence": 0, "error": str(e)}
        rows.append(result)
        progress.progress((i + 1) / len(watchlist), text=f"{symbol} done")
    progress.empty()

    result_df = pd.DataFrame(rows)
    result_df["date"] = datetime.now().strftime("%Y-%m-%d")
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
