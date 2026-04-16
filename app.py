import streamlit as st
import requests
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ Diagnostic", layout="wide")
# PASTE YOUR KEY HERE
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ Diagnostic Terminal")

# Sidebar for testing
ticker = st.sidebar.text_input("TEST SYMBOL", value="INTC").upper().strip()
run_test = st.sidebar.button("RUN CONNECTION DIAGNOSTIC")

if run_test:
    st.info(f"Testing connectivity for {ticker}...")
    
    # We use the most basic endpoint possible to check the key's health
    endpoints = [
        f"quote/{ticker}",
        f"company-outlook?symbol={ticker}"
    ]
    
    for ep in endpoints:
        url = f"{BASE_URL}/{ep}&apikey={API_KEY}" if "?" in ep else f"{BASE_URL}/{ep}?apikey={API_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                st.success(f"✅ {ep}: Accessible")
                st.json(response.json())
            elif response.status_code == 403:
                st.error(f"🚫 {ep}: 403 FORBIDDEN")
                st.write("Reason: Your key is active, but FMP has locked this specific data/ticker for free users.")
            elif response.status_code == 401:
                st.error(f"❌ {ep}: 401 UNAUTHORIZED")
                st.write("Reason: The API Key itself is invalid or has not synced after your password reset.")
            else:
                st.warning(f"⚠️ {ep}: Status {response.status_code}")
                
            time.sleep(2.0) # Safety delay between diagnostic calls
            
        except Exception as e:
            st.error(f"Connection Failed: {e}")

st.divider()
st.subheader("How to fix a persistent 403:")
st.markdown("""
1. **Check Ticker Status:** If `INTC` works but `NKE` or `AAPL` doesn't, you must upgrade your FMP plan to access "Blue Chip" stocks.
2. **Account Verification:** Ensure you clicked the **verification link** in the email FMP sent when you signed up or reset your password.
3. **Daily Limit:** On the free tier, you only get **250 requests per day**. If you hit this limit while testing, the server will return a 403 until midnight.
""")
