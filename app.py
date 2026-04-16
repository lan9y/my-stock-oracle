import streamlit as st
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ Reset", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" # If you got a new key, put it here
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ Connection Test")

ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("TEST CONNECTION")

if run_btn:
    with st.spinner('Testing single-stream connection...'):
        try:
            # ONLY ONE CALL TO START
            url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
            res = requests.get(url, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if data and len(data) > 0:
                    prof = data[0]
                    st.success(f"Connected! Data found for {prof.get('companyName')}")
                    st.write(f"**Current Price:** ${prof.get('price')}")
                    st.write(f"**Description:** {prof.get('description')}")
                else:
                    st.warning("API returned empty. The ticker might be restricted on free tier.")
            elif res.status_code == 429:
                st.error("Rate Limit (429): You are still being throttled by the server.")
            else:
                st.error(f"Server Error: {res.status_code}")
                
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
