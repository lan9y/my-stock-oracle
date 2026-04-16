import streamlit as st
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ Final Test", layout="wide")
# YOUR KEY HAS BEEN INSERTED BELOW
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ Final Connection Test")

ticker = st.sidebar.text_input("SYMBOL", value="INTC").upper().strip()
run_btn = st.sidebar.button("RUN TEST")

if run_btn:
    with st.spinner('Testing access for your specific Key...'):
        try:
            # Test 1: Basic Quote (Should work if key is active)
            q_url = f"{BASE_URL}/quote/{ticker}?apikey={API_KEY}"
            res = requests.get(q_url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data:
                    st.success(f"✅ KEY IS ACTIVE. Data found for {data[0].get('name')}")
                    st.metric("Current Price", f"${data[0].get('price')}")
                else:
                    st.warning("⚠️ Key is working, but this ticker (like NVDA/AAPL) might be paywalled. Try INTC or CSCO.")
            elif res.status_code == 403:
                st.error("❌ 403 FORBIDDEN: The server is still rejecting this specific Key.")
            else:
                st.error(f"Error: {res.status_code}")
                
        except Exception as e:
            st.error(f"Network error: {e}")
