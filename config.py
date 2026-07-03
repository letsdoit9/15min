"""
CONFIG FILE
============
Yaha apni settings edit karo. Baaki files me kuch touch karne ki zarurat nahi.
"""

# ---------------------------------------------------------
# Upstox instrument keys (format: NSE_EQ|ISIN)
# Apne watchlist ke stocks ka instrument_key Upstox instrument
# master file se nikalo: https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz
# Neeche kuch popular Nifty stocks ke examples diye hain - inko apni list se replace/expand karo
# ---------------------------------------------------------
WATCHLIST = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "INFY": "NSE_EQ|INE009A01021",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    # Yaha aur stocks add karo: "SYMBOL": "instrument_key"
}

# ---------------------------------------------------------
# Opening Range settings
# ---------------------------------------------------------
CANDLE_INTERVAL_UNIT = "minutes"
CANDLE_INTERVAL_VALUE = "5"          # 5-minute candles
OPENING_RANGE_CANDLES = 3            # pehli 3 candles = 9:15-9:30
BREAKOUT_CHECK_CANDLE_INDEX = 3      # 4th candle (index 3) = 9:30-9:35, breakout yaha check hoga

# ---------------------------------------------------------
# Screener thresholds (rule-based, no ML abhi)
# ---------------------------------------------------------
MIN_VOLUME_RATIO = 1.3       # breakout candle ka volume, average se kam se kam kitna guna ho
MIN_BODY_PERCENT = 50        # candle body, uski total range ka kam se kam kitna % ho
MIN_RANGE_PERCENT = 0.3      # opening range, stock price ka kam se kam kitna % ho (bahut chota range skip karo)
MAX_RANGE_PERCENT = 3.0      # bahut zyada wide range bhi skip karo (already volatile / news wala din)

# Trend score normalization range (%) - continuous scoring ke liye
# (EMA20-EMA50 + VWAP bias) ka combined % value is range se bahar ho to
# score 0 ya 25 pe clamp ho jaata hai. Chhota range = zyada sensitive scoring.
TREND_NORMALIZE_RANGE_PCT = 1.0

# ---------------------------------------------------------
# Output
# ---------------------------------------------------------
OUTPUT_DIR = "output"
LOG_CSV = "output/screener_log.csv"    # har din ka result yaha append hota rahega -> future ML training data

# ---------------------------------------------------------
# Telegram alerts (optional - baad me fill karna)
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
