import streamlit as st
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
NEW_API_KEY = "PASTE_YOUR_NEW_KEY_HERE" # <--- GET A FRESH KEY
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ VMI Terminal")

ticker = st.sidebar.text_input("SYMBOL", value="INTC").upper().strip()
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    with st.spinner('Accessing Open Data...'):
        try:
            # TRY QUOTE INSTEAD OF PROFILE (Bypasses many 403s)
            q = requests.get(f"{BASE_URL}/quote/{ticker}?apikey={NEW_API_KEY}").json()
            time.sleep(3.0) # Mandatory delay
            
            # TRY RATIOS (Usually open for free users)
            r = requests.get(f"{BASE_URL}/ratios-ttm/{ticker}?apikey={NEW_API_KEY}").json()

            if q and isinstance(q, list):
                stock = q[0]
                ratio = r[0] if r else {}
                
                st.header(f"{stock.get('name')} ({ticker})")
                st.metric("Price", f"${stock.get('price')}", f"{stock.get('changesPercentage')}%")
                
                # --- VMI LOGIC ---
                st.subheader("VMI Quick Stats")
                c1, c2 = st.columns(2)
                c1.write(f"**Market Cap:** ${round(stock.get('marketCap', 0)/1e9, 2)}B")
                c2.write(f"**ROIC (TTM):** {round(ratio.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%")
                
                st.success("✅ Connection Restored with New Key.")
            else:
                st.error("403 Forbidden: Even with a new key, this ticker is restricted. Try INTC, CSCO, or TSLA.")
        except Exception as e:
            st.error(f"Sync Error: {e}")
