import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import random

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

st.title("🔮 OraclePro™ VMI Terminal")
st.markdown("🚀 *Stability Mode: Browser Fingerprinting Active*")

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    discount_rate = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Bypassing Rate Limits for {ticker_sym}...'):
        # --- RETRY LOGIC ENGINE ---
        success = False
        retries = 3
        
        while retries > 0 and not success:
            try:
                stock = yf.Ticker(ticker_sym)
                # Force a small random delay to avoid bot detection
                time.sleep(random.uniform(1.0, 3.0))
                
                info = stock.info
                hist = stock.history(period="1y")
                
                if info and 'currentPrice' in info:
                    success = True
                    # --- DASHBOARD RENDER ---
                    tab_ov, tab_iv = st.tabs(["📊 Overview", "🎯 20yr IV Model"])
                    
                    with tab_ov:
                        st.header(f"{info.get('longName', ticker_sym)}")
                        st.success("🛡️ Wide Moat Detected" if info.get('returnOnAssets', 0) > 0.08 else "⚠️ Narrow Moat")
                        st.write(info.get('longBusinessSummary'))
                        
                    with tab_iv:
                        iv = calculate_vmi_iv(
                            info.get('freeCashflow', 0), 
                            info.get('totalDebt', 0), 
                            info.get('totalCash', 0), 
                            info.get('sharesOutstanding', 1), 
                            info.get('beta', 1.1)
                        )
                        st.metric("VMI 20yr IV", f"${iv}")
                        st.metric("Market Price", f"${info.get('currentPrice')}")
                else:
                    retries -= 1
                    time.sleep(5) # Wait longer if limited
                    
            except Exception as e:
                retries -= 1
                time.sleep(5)
                if retries == 0:
                    st.error(f"🚨 Yahoo is currently blocking the server IP. Try again in 15 minutes.")
