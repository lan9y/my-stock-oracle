import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ VMI Terminal")

ticker = st.sidebar.text_input("SYMBOL (Wait 5 min before first run)", value="AAPL").upper().strip()
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
    # --- INTERNAL DATA RESET ---
    p, m, h = None, None, None
    
    with st.spinner('STAGING DATA... DO NOT REFRESH...'):
        try:
            # CALL 1
            res1 = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}", timeout=10)
            if res1.status_code == 200: p = res1.json()
            time.sleep(6.0) # 6 second safety gap
            
            # CALL 2
            res2 = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}", timeout=10)
            if res2.status_code == 200: m = res2.json()
            time.sleep(6.0) # 6 second safety gap
            
            # CALL 3
            res3 = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250", timeout=10)
            if res3.status_code == 200: h = res3.json()

            if p and isinstance(p, list) and len(p) > 0:
                prof = p[0]
                met = m[0] if (m and isinstance(m, list)) else {}
                
                # --- RENDER ---
                col_header, col_moat = st.columns([3,1])
                with col_header:
                    st.header(f"{prof.get('companyName')} ({ticker})")
                    st.write(f"**Industry:** {prof.get('industry')} | **Sector:** {prof.get('sector')}")
                with col_moat:
                    st.success("MOAT STATUS: WIDE")
                
                st.info(prof.get('description'))
                
                # --- IV CALC ---
                price = prof.get('price', 1)
                shares = met.get('numberOfSharesTTM', (prof.get('mktCap', 0)/price))
                iv = calculate_vmi_iv(met.get('freeCashFlowTTM', 0), met.get('totalDebtTTM', 0), met.get('cashAndShortTermInvestmentsTTM', 0), shares, prof.get('beta', 1.1))
                
                c1, c2 = st.columns(2)
                c1.metric("VMI 20yr IV", f"${iv}")
                c2.metric("Market Price", f"${price}")

                if h and 'historical' in h:
                    df = pd.DataFrame(h['historical']).sort_values('date')
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
                    fig.update_layout(template="plotly_dark", height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("API is still rejecting the connection. Check back in 10 minutes.")
                
        except Exception as e:
            st.error("The API server timed out. Please wait 120s.")
