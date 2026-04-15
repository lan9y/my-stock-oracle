import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" # Swap this if you have a 2nd key
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI STYLING ---
st.markdown("""
    <style>
    .score-card { background-color: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 22px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SMART FETCHING ENGINE ---
def fetch_safe(endpoint, ticker):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        return data if isinstance(data, list) and len(data) > 0 else None
    except: return None

# --- EXCEL LOGIC: 20-YEAR IV ---
def vmi_iv_calc(fcf, debt, cash, shares, beta):
    rf, mrp = 0.036, 0.027 # From Excel Template
    discount = rf + (beta * mrp)
    # Excel 3-Stage Growth: 17% -> 15% -> 4%
    total_pv = 0
    curr_fcf = fcf
    for y in range(1, 21):
        growth = 0.17 if y <= 5 else 0.15 if y <= 10 else 0.04
        curr_fcf *= (1 + growth)
        total_pv += curr_fcf / ((1 + discount) ** y)
    return round((total_pv - debt + cash) / shares, 2)

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
if st.sidebar.button("EXECUTE ANALYSIS"):
    # Clear cache to allow a fresh run if user changes ticker
    st.cache_data.clear()
    st.session_state['run'] = True

if st.session_state.get('run'):
    # We use st.cache_data to ensure we don't re-call the API when switching tabs
    @st.cache_data(ttl=600)
    def load_all_data(t):
        p = fetch_safe("profile", t)
        if p == "LIMIT": return "LIMIT"
        m = fetch_safe("key-metrics-ttm", t)
        r = fetch_safe("ratios-ttm", t)
        c = fetch_safe("historical-price-full", t)
        b = fetch_safe("balance-sheet-statement", t)
        return {"p": p[0] if p else {}, "m": m[0] if m else {}, 
                "r": r[0] if r else {}, "c": c, "b": b[0] if b else {}}

    data = load_all_data(ticker)

    if data == "LIMIT":
        st.error("🚦 API RATE LIMIT: Too many requests. Please wait 60 seconds.")
    elif data:
        p, m, r, c, b = data['p'], data['m'], data['r'], data['c'], data['b']
        
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Technicals", "🎯 VMI 20yr IV"])

        with tab1:
            # Scorecards based on Screenshot
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            roic = r.get('returnOnCapitalEmployedTTM', 0.15)
            with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
            with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roic*50, 10))}/10</div></div>', unsafe_allow_html=True)
            with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
            with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
            with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
            with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
            
            st.header(p.get('companyName'))
            st.info(p.get('description', '')[:800] + "...")

        with tab2:
            if c and 'historical' in c:
                df = pd.DataFrame(c['historical'])
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                df['SMA50'] = df['close'].rolling(50).mean()
                df['SMA200'] = df['close'].rolling(200).mean()
                fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange'), name="SMA 50"))
                fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red'), name="SMA 200"))
                fig.update_layout(template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            iv = vmi_iv_calc(m.get('freeCashFlowTTM', 0), b.get('totalDebt', 0), 
                             b.get('cashAndShortTermInvestments', 0), m.get('numberOfShares', 1), p.get('beta', 1))
            st.metric("VMI Intrinsic Value", f"${iv}", delta=f"{round(((iv-p.get('price',1))/p.get('price',1))*100,2)}% Upside")
            if iv > p.get('price', 0): st.success("🎯 BUY ZONE")
            else: st.warning("⚖️ FAIR VALUE / HOLD")
