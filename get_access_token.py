"""
GET ACCESS TOKEN
================
Ise HAR TRADING DAY ek baar subah chalao (market khulne se pehle).
Upstox ka access token daily expire hota hai, isliye roz naya lena padta hai.

Pehli baar chalane se pehle .env file banao is folder me, is tarah:

    UPSTOX_API_KEY=your_api_key_here
    UPSTOX_API_SECRET=your_api_secret_here
    UPSTOX_REDIRECT_URI=https://127.0.0.1/callback

(API key/secret Upstox developer console se milega: https://account.upstox.com/developer/apps)
Redirect URI wahi daalo jo apne Upstox app banate waqt register kiya tha.

Chalane ka tareeka:  python get_access_token.py
"""

import os
import webbrowser
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

if not API_KEY or not API_SECRET or not REDIRECT_URI:
    print("ERROR: .env file me UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_REDIRECT_URI set karo pehle.")
    raise SystemExit(1)

# Step 1: Login URL browser me kholo
auth_url = (
    f"https://api.upstox.com/v2/login/authorization/dialog"
    f"?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
)

print("Browser me Upstox login page khul raha hai...")
print("Agar khud na khule to ye link manually browser me paste karo:\n")
print(auth_url, "\n")
webbrowser.open(auth_url)

print("Login karne ke baad browser address bar me URL kuch aisa dikhega:")
print(f"  {REDIRECT_URI}?code=XXXXXXXX\n")
auth_code = input("Us URL me se 'code=' ke baad wala part yaha paste karo: ").strip()

# Step 2: Code ko access token se exchange karo
token_url = "https://api.upstox.com/v2/login/authorization/token"
payload = {
    "code": auth_code,
    "client_id": API_KEY,
    "client_secret": API_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}
headers = {"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}

response = requests.post(token_url, data=payload, headers=headers)

if response.status_code == 200:
    access_token = response.json()["access_token"]
    # .env file me save kar do taaki baaki scripts ise read kar sake
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    set_key(env_path, "UPSTOX_ACCESS_TOKEN", access_token)
    print("\n✅ Access token mil gaya aur .env file me save ho gaya.")
    print("Ab aap main.py chala sakte ho.")
else:
    print("\n❌ Token generate nahi hua. Error:")
    print(response.status_code, response.text)
