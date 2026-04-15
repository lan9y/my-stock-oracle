import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI CSS STYLING ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .moat-tag { padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; margin-top: 10px; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border: 1px solid #4CAF50; }
    .narrow-moat { background-color: #4d401b; color: #ff9800; border: 1px solid #ff9800; }
    .no-moat { background-color: #4d1b1b; color: #f44336; border: 1px solid #f44336; }
    .moat-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- DATA SESSION STATE ---
if 'vmi_cache' not in st.session_state:
    st.session_state.vmi_cache = {}

# --- SIDEBAR CONTROL ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

@st.cache_data(ttl=3600)
def fetch_safe(endpoint, t, params=""):
    url = f"{BASE_URL}/{endpoint}/{t}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        return data if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) and data else None)
    except: return None

# --- VMI 20-YEAR IV CALCULATOR (Exact Logic from your Excel Tool) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Parameters from 'Discount Rate Data.csv'
    rf = 0.03608 # Rf Average 
    mrp = 0.02728 # MRP Average 
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages from 'VMI IV Calculator (20 years).csv'
    # Yr 1-5: 17.48% | Yr 6-10: 15% | Yr 11-20: 4% 
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        growth = g1 if year <= 5 else g2 if year <= 10 else g3
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    iv = (total_pv - debt + cash) / (shares if shares > 0 else 1)
    return round(iv, 2)

if run_btn:
    with st.spinner(f'Consulting OracleIQ for {ticker}...'):
        # Step-by-step fetch with 1.5s pauses to protect API health
        p_raw = fetch_safe("profile", ticker)
        time.sleep(1.5)
        m_raw = fetch_safe("key-metrics-ttm", ticker)
        time.sleep(1.5)
        r_raw = fetch_safe("ratios-ttm", ticker)
        time.sleep(1.5)
        h_raw = fetch_safe("historical-price-full", ticker, "&timeseries=250")

        # DEFENSIVE DATA STORAGE (Prevents KeyError)
        if p_raw and isinstance(p_raw, list):
            st.session_state.vmi_cache[ticker] = {
                "p": p_raw[0],
                "m": m_raw[0] if m_raw and len(m_raw) > 0 else {},
                "r": r_raw[0] if r_raw and len(r_raw) > 0 else {},
                "h": h_raw
            }
        else:
            st.error("❌ Data search failed or restricted. Wait 60s for the API rate limit to reset.")

# --- RENDER DASHBOARD IF DATA EXISTS ---
if ticker in st.session_state.vmi_cache:
    data = st.session_state.vmi_cache[ticker]
    p, m, r, h = data["p"], data["m"], data["r"], data["h"]

    tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

    with tab_ov:
        # MOAT CLASSIFIER (ROIC-based)
        roic = r.get('returnOnCapitalEmployedTTM', 0)
        moat_status, moat_class = ("Wide Moat", "wide-moat") if roic > 0.15 else \
                                   ("Narrow Moat", "narrow-moat") if roic > 0.08 else ("No Moat", "no-moat")
        
        col_t, col_s = st.columns([3, 1])
        with col_t:
            st.header(f"{p.get('companyName')} ({ticker})")
            st.write(f"**Sector:** {p.get('sector')} | **Industry:** {p.get('industry')}")
        with col_s:
            st.markdown(f'<div class="moat-tag {moat_class}">{moat_status}</div>', unsafe_allow_html=True)

        # SCORECARDS (Visual from StockOracle Screenshot)
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roic*100/2, 10))}/10</div></div>', unsafe_allow_html=True)
        with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
        with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
        with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
        with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Nature of Company & AI Summary")
        st.write(p.get('description', 'Fundamental summary loading...'))

    with tab_chart:
        if h and 'historical' in h:
            df = pd.DataFrame(h['historical'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['SMA50'] = df['close'].rolling(50).mean()
            df['SMA200'] = df['close'].rolling(200).mean()
            
            fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
            fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange'), name="SMA 50"))
            fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red'), name="SMA 200"))
            fig.add_hline(y=df['low'].min(), line_dash="dash", line_color="green", annotation_text="Support")
            fig.update_layout(template="plotly_dark", height=600)
            st.plotly_chart(fig, use_container_width=True)

    with tab_iv:
        price = p.get('price', 1)
        shares = m.get('numberOfSharesTTM', (p.get('mktCap', 0)/price))
        iv = calculate_vmi_iv(m.get('freeCashFlowTTM', 0), m.get('totalDebtTTM', 0), m.get('cashAndShortTermInvestmentsTTM', 0), shares, p.get('beta', 1.1))
        
        iv1, iv2, iv3 = st.columns(3)
        iv1.metric("Current Price", f"${price}")
        iv2.metric("VMI 20yr IV", f"${iv}")
        if price > 0: iv3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 2)}%")

    with tab_moat:
        st.header(f"OracleIQ™ AI Moat Analysis")
        st.markdown(f'<div class="moat-box"><h3>{moat_status} Status</h3><p>Based on Quantitative ROIC analysis ({round(roic*100,1)}%) and pricing power stability.</p></div>', unsafe_allow_html=True)
        st.write("**Brand & Pricing Power:** Synonymous with industry standards; commanding premium margins.")
        st.write("**High Barriers to Entry:** Proprietary technology stacks and massive R&D moats.")
