import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .moat-tag { padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; margin-top: 10px; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border: 1px solid #4CAF50; }
    .narrow-moat { background-color: #4d401b; color: #ff9800; border: 1px solid #ff9800; }
    .no-moat { background-color: #4d1b1b; color: #f44336; border: 1px solid #f44336; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- DATA SESSION STATE (The Shield) ---
if 'stock_oracle_cache' not in st.session_state:
    st.session_state.stock_oracle_cache = None

ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR (Exact Excel Logic) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 # Your Excel Constants
    discount_rate = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Your 3-Stage Growth
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    st.session_state.stock_oracle_cache = None # Clear old data
    with st.spinner(f'Sequential Sync: Stay on this page for 10 seconds...'):
        try:
            # STEP 1: Profile
            p = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}").json()
            time.sleep(3.0) # Long pause to satisfy the server gate
            
            # STEP 2: Metrics
            m = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}").json()
            time.sleep(3.0)
            
            # STEP 3: Ratios
            r = requests.get(f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}").json()
            time.sleep(3.0)
            
            # STEP 4: History
            h = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250").json()

            if p and isinstance(p, list):
                st.session_state.stock_oracle_cache = {
                    "prof": p[0], "met": m[0] if m else {},
                    "rat": r[0] if r else {}, "hist": h
                }
            else:
                st.error("🚦 API Gate Locked. Wait 60s and try again.")
        except:
            st.error("Network sync failed. Please check ticker.")

# --- RENDER DASHBOARD ---
if st.session_state.stock_oracle_cache:
    sd = st.session_state.stock_oracle_cache
    prof, met, rat, hist = sd["prof"], sd["met"], sd["rat"], sd["hist"]

    tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 VMI Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

    with tab_ov:
        # MOAT STATUS (Logic based on ROIC & Margin)
        roic = rat.get('returnOnCapitalEmployedTTM', 0)
        moat_status, moat_class = ("Wide Moat", "wide-moat") if roic > 0.18 else ("Narrow Moat", "narrow-moat") if roic > 0.09 else ("No Moat", "no-moat")
        
        col_t, col_s = st.columns([3, 1])
        with col_t:
            st.header(f"{prof.get('companyName')} ({ticker})")
            st.write(f"**Sector:** {prof.get('sector')} | **Industry:** {prof.get('industry')}")
        with col_s:
            st.markdown(f'<div class="moat-tag {moat_class}">{moat_status}</div>', unsafe_allow_html=True)

        # SCORECARDS
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roic*100/2, 10))}/10</div></div>', unsafe_allow_html=True)
        with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
        with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
        with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
        with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Nature of Company & Segment Deep-Dive")
        st.write(prof.get('description'))

    with tab_chart:
        if hist and 'historical' in hist:
            df = pd.DataFrame(hist['historical']).sort_values('date')
            df['date'] = pd.to_datetime(df['date'])
            fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
            fig.add_trace(go.Scatter(x=df['date'], y=df['close'].rolling(50).mean(), line=dict(color='orange'), name="SMA 50"))
            fig.add_trace(go.Scatter(x=df['date'], y=df['close'].rolling(200).mean(), line=dict(color='red'), name="SMA 200"))
            fig.update_layout(template="plotly_dark", height=600)
            st.plotly_chart(fig, use_container_width=True)

    with tab_iv:
        cur_p = prof.get('price', 1)
        shares = met.get('numberOfSharesTTM', (prof.get('mktCap', 0)/cur_p))
        iv = calculate_vmi_iv(met.get('freeCashFlowTTM', 0), met.get('totalDebtTTM', 0), met.get('cashAndShortTermInvestmentsTTM', 0), shares, prof.get('beta', 1.1))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Price", f"${cur_p}")
        c2.metric("VMI 20yr IV", f"${iv}")
        if cur_p > 0: c3.metric("Margin of Safety", f"{round(((iv-cur_p)/cur_p)*100, 2)}%")
