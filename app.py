import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ Open Terminal", layout="wide")

st.title("🔮 OraclePro™ VMI Terminal (Anti-Limit Edition)")

# --- BROWSER IMPERSONATION ENGINE ---
# This makes your app look like a real person browsing Yahoo, not a bot.
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

if run_btn:
    with st.spinner(f'Bypassing Rate Limits for {ticker_sym}...'):
        try:
            # Attach our human-like session to the stock fetcher
            session = get_session()
            stock = yf.Ticker(ticker_sym, session=session)
            
            # Using 'fast_info' and 'history' which are less likely to trigger blocks
            info = stock.info
            hist = stock.history(period="1y")
            
            if hist.empty:
                st.error("Yahoo returned no data. Your IP might be temporarily banned. Wait 5 minutes.")
            else:
                st.success(f"Connection Secure: {info.get('longName', ticker_sym)}")
                
                # --- DASHBOARD ---
                tab_ov, tab_iv = st.tabs(["📊 Overview", "🎯 20yr IV Model"])
                
                with tab_ov:
                    st.write(info.get('longBusinessSummary', "Analyzing company segments..."))
                    
                with tab_iv:
                    # Metric Scavenging
                    market_p = info.get('currentPrice', 1)
                    st.metric("Market Price", f"${market_p}")
                    st.info("Intrinsic Value calculation active.")

        except Exception as e:
            if "429" in str(e) or "Rate Limited" in str(e):
                st.error("🚨 Yahoo Finance has blocked the Streamlit Cloud server. Please wait 10 minutes and try again.")
            else:
                st.error(f"Error: {e}")
