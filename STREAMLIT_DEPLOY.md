# GitHub + Streamlit Cloud Pe Deploy Karna (Free, Browser-Only, Kuch Install Nahi)

Isse tumhara screener ek website ki tarah kaam karega — kisi bhi browser se kholo,
login karo, screener chalao, CSV download karo. Laptop me Python install karne ki
zarurat nahi.

---

## Step 1: GitHub Account Banao

1. https://github.com/signup pe jaake free account banao (agar pehle se nahi hai)

## Step 2: Naya Repository Banao

1. Login karke top-right me **"+"** icon → **"New repository"**
2. Naam do: `orb-screener` (ya kuch bhi)
3. **Private** select karo (important — ye tumhara trading tool hai, public mat rakho)
4. **"Create repository"** click karo

## Step 3: Files Upload Karo (Bina Command Line Ke)

1. Naye repo page pe **"uploading an existing file"** link dikhega — uspe click karo
2. Ye saari files ek saath drag-drop karo:
   - `streamlit_app.py`
   - `config.py`
   - `screener.py`
   - `indicators.py`
   - `upstox_client.py`
   - `get_access_token.py`
   - `fetch_nifty50_instruments.py`
   - `requirements.txt`
   - `README.md`

   ⚠️ **`.env` file MAT upload karna** (agar tumne bana li hai) — usme secrets hote hain

3. Neeche **"Commit changes"** click karo

## Step 3.5: Nifty50 Watchlist Keys Nikalo (Ek Baar Karna Hai)

Tumhare paas local Python nahi hai, isliye ye ek chhota step **Google Colab** (free, browser-only) pe karo:

1. https://colab.research.google.com/ pe jaao, naya notebook banao
2. `fetch_nifty50_instruments.py` file upload karo (📁 icon se)
3. Cell me chalao:
```python
!pip install requests
!python fetch_nifty50_instruments.py
```
4. `config_watchlist_nifty50.txt` file generate hogi — usse download karo (ya seedha khol ke content copy karo)
5. Us content ko GitHub repo ki `config.py` file me jaake, `WATCHLIST = {...}` wale part ko replace karke paste kar do (GitHub pe file edit karne ke liye us file ko kholo aur pencil ✏️ icon click karo)

Ye sirf ek baar karna hai (jab tak Nifty50 composition badle na, jo saal me 1-2 baar hota hai).

## Step 4: Streamlit Community Cloud Pe Deploy Karo

1. Jaao: **https://share.streamlit.io/**
2. **"Sign up"** / **"Continue with GitHub"** — apne GitHub account se login karo (permission maango to allow karo)
3. **"Create app"** → **"Deploy a public app from GitHub"**
4. Apna repo select karo (`orb-screener`)
5. Main file path me likho: `streamlit_app.py`
6. **"Deploy"** click karo

2-3 minute me app deploy ho jayega aur tumhe ek URL milega jaisa:
`https://your-app-name.streamlit.app`

**Ye URL hi tumhara "redirect URI" banega — isse yaad rakho.**

## Step 5: Secrets Set Karo (API Key Safely Store Karna)

Deploy hone ke baad:

1. App ke dashboard me **"Settings"** (⚙️) → **"Secrets"**
2. Yaha paste karo (apni actual values ke saath):

```toml
UPSTOX_API_KEY = "your_api_key_here"
UPSTOX_API_SECRET = "your_api_secret_here"
UPSTOX_REDIRECT_URI = "https://your-app-name.streamlit.app"
```

3. Save karo — app automatically restart ho jayega

## Step 6: Upstox App Me Redirect URI Update Karo

1. https://account.upstox.com/developer/apps pe jaao
2. Apna app kholo, **Redirect URI** ko update karo — wahi URL daalo jo Step 4 me mila
   (`https://your-app-name.streamlit.app`)
3. Save karo

## Step 7: Use Karo!

1. Apna app URL browser me kholo: `https://your-app-name.streamlit.app`
2. **"Upstox se Login Karo"** button click karo
3. Upstox login karo → automatically wapas apne app pe aa jaoge, logged in
4. Watchlist check/edit karo
5. 9:35 AM ke baad **"Run Screener Now"** click karo
6. Results dekho, phir **"Download CSV"** click karke apne laptop me ek folder me save kar lo

---

## Roz Ka Workflow (Ab Se Ye Karna Hai)

1. Apna app URL browser me kholo (bookmark kar lo)
2. Login karo (roz karna padega — token daily expire hota hai)
3. 9:35 baad "Run Screener Now" click karo
4. CSV download karke save karo — is naam se rakho jaise `screener_log_2026-07-03.csv`

## ⚠️ Important Baatein

- **Data persist nahi hota** — jab bhi app restart/sleep hota hai (Streamlit free tier
  thodi der inactive rehne par sleep ho jaata hai), session ka data khatam ho jaata hai.
  Isliye CSV download karna zaroori hai, har baar.
- **Multiple baar din me chala sakte ho** — agar 10:15, 11:00 pe bhi check karna hai,
  bas "Run Screener Now" phir se click karo, naya data add hota jayega usi session me.
- **Private repo rakho** — API key/secret Streamlit Secrets me safe hai, lekin phir bhi
  repo ko public mat karna.

---

Jab CSV files jama karte jaana (1500-2000+ rows), mujhe bata dena — ML training wala
Phase 4 bana denge.
