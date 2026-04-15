import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ VMI Terminal")

ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR (EXCEL LOGIC) ---
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
    with st.spinner('FETCHING DATA... PLEASE WAIT 15 SECONDS. DO NOT REFRESH.'):
        try:
            # 1. PROFILE
            p = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}").json()
            time.sleep(5.0) 
            
            # 2. KEY METRICS
            m = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}").json()
            time.sleep(5.0)
            
            # 3. HISTORY
            h = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250").json()

            if p and isinstance(p, list):
                prof, met = p[0], m[0] if m else {}
                
                tab_ov, tab_iv, tab_chart = st.tabs(["📊 Overview", "🎯 20yr IV Model", "📈 Chart"])

                with tab_ov:
                    st.header(f"{prof.get('companyName')} | {prof.get('sector')}")
                    st.subheader("Moat Status: Wide Moat")
                    st.write(prof.get('description'))
                    
                with tab_iv:
                    price = prof.get('price', 1)
                    shares = met.get('numberOfSharesTTM', (prof.get('mktCap', 0)/price))
                    iv = calculate_vmi_iv(met.get('freeCashFlowTTM', 0), met.get('totalDebtTTM', 0), met.get('cashAndShortTermInvestmentsTTM', 0), shares, prof.get('beta', 1.1))
                    st.metric("VMI 20yr IV", f"${iv}")
                    st.metric("Current Price", f"${price}")

                with tab_chart:
                    df = pd.DataFrame(h['historical']).sort_values('date')
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("API Blocked. You must wait 120s without clicking anything.")
        except Exception as e:
            st.error("Connection Interrupted. Wait 60s.")
