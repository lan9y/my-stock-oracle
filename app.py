import streamlit as st
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ Institutional Terminal")

ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE ANALYSIS")

if analyze_btn:
    with st.spinner('Accessing Oracle Data...'):
        # Safety Check: We only fetch the MOST IMPORTANT data to save credits
        url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
        
        try:
            response = requests.get(url)
            
            # If the server says "Too many requests" (Error 429)
            if response.status_code == 429:
                st.error("🚦 SLOW DOWN: You've hit the per-minute limit. Wait 60 seconds.")
            
            elif response.status_code == 403:
                st.error("🚫 LIMIT REACHED: You've used all 250 daily credits.")
                
            else:
                data = response.json()
                if data:
                    stock = data[0]
                    st.header(stock.get('companyName'))
                    st.metric("Current Price", f"${stock.get('price')}")
                    # ... (rest of your UI here)
                else:
                    st.warning("⚠️ No data found for this ticker.")
                    
        except Exception as e:
            st.error("🌐 Connection Issue. Please check your internet or API key.")
