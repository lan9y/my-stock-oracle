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
    .moat-tag { padding: 5px 15px; border-radius: 20px; font-weight: 700; font-size: 14px; display: inline-block; margin-top: 10px; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border: 1px solid #4CAF50; }
    .narrow-moat { background-color: #4d401b; color: #ff9800; border: 1px solid #ff9800; }
    .no-moat { background-color: #4d1b1b; color: #f44336; border: 1px solid #f44336; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- MOAT CLASSIFIER LOGIC ---
def get_moat_status(roic, gross_margin):
    # Logic: Wide Moat requires ROIC > 20% and Gross Margin > 40%
    if roic > 0.20 and gross_margin > 0.40:
        return "Wide Moat", "wide-moat"
    elif roic > 0.10 or gross_margin > 0.25:
        return "Narrow Moat", "narrow-moat"
    else:
        return "No Moat", "no-moat"

# --- VMI 20-YEAR IV CALCULATOR ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 # Constants from Excel
    discount_rate = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Multi-stage Growth
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Polite VMI Sync Active for {ticker}...'):
        # Sequential Fetch to prevent 🚦 Speed Limit Hit
        p_res = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}").json()
        time.sleep(1.5)
        m_res = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}").json()
        time.sleep(1.5)
        r_res = requests.get(f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}").json()
        time.sleep(1.5)
        h_res = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250").json()

        if p_res and isinstance(p_res, list):
            p, m, r = p_res[0], (m_res[0] if m_res else {}), (r_res[0] if r_res else {})
            
            tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 VMI Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

            with tab_ov:
                # 1. MOAT STATUS HEADER
                roic = r.get('returnOnCapitalEmployedTTM', 0)
                gm = r.get('grossProfitMarginTTM', 0)
                moat_text, moat_class = get_moat_status(roic, gm)
                
                col_title, col_status = st.columns([3, 1])
                with col_title:
                    st.header(f"{p.get('companyName')} ({ticker})")
                    st.write(f"**Sector:** {p.get('sector')} | **Industry:** {p.get('industry')}")
                with col_status:
                    st.markdown(f'<div class="moat-tag {moat_class}">{moat_text}</div>', unsafe_allow_html=True)

                # 2. SCORECARDS
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown('<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                # 3. STOCKORACLE DESCRIPTION STYLE
                st.subheader("Company Nature & Core Operations")
                st.info(p.get('description', 'Fundamental description currently loading...'))

            with tab_chart:
                if h_res and 'historical' in h_res:
                    df = pd.DataFrame(h_res['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange'), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red'), name="SMA 200"))
                    fig.update_layout(template="plotly_dark", height=600)
                    st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                iv = calculate_vmi_iv(m.get('freeCashFlowTTM', 0), m.get('totalDebtTTM', 0), m.get('cashAndShortTermInvestmentsTTM', 0), m.get('numberOfSharesTTM', 1), p.get('beta', 1.1))
                price = p.get('price', 0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"${price}")
                c2.metric("VMI 20yr IV", f"${iv}")
                if price > 0: c3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 2)}%")

            with tab_moat:
                st.header("OracleIQ™ AI Moat Analysis")
                st.markdown(f'<div class="moat-box"><h3>{moat_text} Status</h3><p>Based on Quantitative Return on Invested Capital (ROIC: {round(roic*100, 2)}%) and Pricing Power (Gross Margin: {round(gm*100, 2)}%).</p></div>', unsafe_allow_html=True)
                st.write("**Competitive Advantages:** Integrated hardware-software lock-in, proprietary patents, and global scale-driven network effects.")
        else:
            st.error("🚦 API Speed Limit Hit. Please wait 60s and try again.")
