# Opening Range Breakout Screener

Rule-based screener jo Upstox API se live data lekar, pehli 3 candles (9:15-9:30) ka
range nikalta hai aur 4th candle (9:30-9:35) pe breakout detect karta hai — bullish/bearish
signal aur confidence score ke saath.

**Ye abhi ML model NAHI hai.** Ye rule-based hai (volume, candle body, VWAP, EMA, RSI ke
combination se score banata hai) aur har din ka data CSV me save karta hai. 2-3 mahine
data collect hone ke baad us CSV se hum ML model train karenge — tab tak ye khud
usable screener ki tarah kaam karega.

---

## Step 1: Python Install Karo

1. https://www.python.org/downloads/ se Python 3.10+ install karo
2. Install karte waqt "Add Python to PATH" checkbox zaroor tick karo (Windows par)
3. Confirm karne ke liye terminal/command prompt me: `python --version`

## Step 2: Ye Folder Kahi Save Karo

Is poore `orb_screener` folder ko apne computer me kisi easy location pe rakho
(jaise `Desktop/orb_screener`)

## Step 3: Required Packages Install Karo

Terminal/Command Prompt kholo, is folder me jaao:

```
cd path/to/orb_screener
pip install -r requirements.txt
```

## Step 4: Upstox Developer App Banao

1. https://account.upstox.com/developer/apps pe jaao (Upstox account se login)
2. "New App" banao
3. Redirect URI me daalo: `https://127.0.0.1/callback` (ya jo bhi tum use karna chahte ho)
4. App banne ke baad tumhe milega: **API Key** aur **API Secret** — inhe copy kar lo

## Step 5: .env File Banao

1. `.env.example` file ko copy karo, naam badal ke `.env` rakho (bina .example ke)
2. Usme apna API Key, API Secret, Redirect URI bharo

## Step 6: Daily Access Token Lo

**Har trading day** market khulne se pehle ye chalao:

```
python get_access_token.py
```

- Browser me Upstox login khulega, login karo
- Login ke baad browser URL me `code=XXXXX` dikhega — wo copy karke terminal me paste karo
- Token automatically `.env` file me save ho jaayega

⚠️ Ye token sirf 1 din valid rehta hai (Upstox ka rule hai), isliye roz subah chalana padega.

## Step 7: Apna Watchlist Set Karo

**Nifty50 (50 stocks) ke liye:**

```
pip install requests
python fetch_nifty50_instruments.py
```

Ye script Upstox ki official instrument list se khud accurate keys nikaal ke
`config_watchlist_nifty50.txt` banayegi. Uska content copy karke `config.py` ke
`WATCHLIST` dictionary me paste kar do (poori dictionary replace kar dena).

⚠️ Script terminal me batayegi agar koi symbol nahi mila (kabhi kabhi NSE pe
ticker/company badalta rehta hai) — un 1-2 stocks ko manually Upstox instrument
file me dhoondh lena ya skip kar dena.

**Custom/apni watchlist ke liye:**

`config.py` file kholo, `WATCHLIST` me apne stocks daalo. Har stock ke liye
"instrument_key" chahiye — ye Upstox ki instrument master file se milta hai:

https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz

## Step 8: Screener Chalao

9:35 AM ke baad (jab 4th candle complete ho chuki ho):

```
python main.py
```

Output terminal me dikhega, aur `output/screener_log.csv` me bhi save hoga.

---

## Roz Ka Workflow

1. Subah market khulne se pehle: `python get_access_token.py`
2. 9:35 AM ke baad: `python main.py`
3. (Optional) Ise repeat kar sakte ho din me multiple baar bhi — jaise 9:35, 10:15,
   11:00 etc. par different opening range windows check karne ke liye
   (iske liye config me thoda change karna hoga — bata dena)

## Agla Step: ML Model

Jab `output/screener_log.csv` me 1500-2000+ rows ho jaayein (matlab kaafi breakout events
record ho chuke hon), tab hum:

1. Us CSV me ek column add karenge — "actual_result" (kya breakout successful raha ya fake)
   — ye tumhe manually ya price check karke bharna hoga shuru me
2. Us labeled data pe XGBoost model train karenge
3. Rule-based confidence score ko ML probability se replace karenge

Jab ready ho, bata dena — main agla phase bana dunga.

---

## Important Disclaimer

- Ye tool sirf analysis/screening ke liye hai, koi trading recommendation nahi deta
- Rule-based confidence score guaranteed accuracy nahi hai — ise ek filter ki tarah use karo,
  apni risk management (stop-loss, position sizing) khud decide karo
- Live trading se pehle kam se kam 1 mahina paper-trading (bina real paisa lagaye) karke
  dekho ki signals kaisa perform karte hain
