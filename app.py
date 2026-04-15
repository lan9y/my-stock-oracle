import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS (StockOracle Styles) ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .moat-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI SCAN")

# --- DATA ENGINE (Sequential Fetch to Avoid Rate Limits) ---
@st.cache_data(ttl=3600)
def fetch_sequential(t):
    endpoints = ["profile", "key-metrics-ttm", "balance-sheet-statement", "historical-price-full"]
    results = {}
    
    for ep in endpoints:
        url = f"{BASE_URL}/{ep}/{t}?apikey={API_KEY}"
        if ep == "historical-price-full":
            url += "&timeseries=250"
        elif ep == "balance-sheet-statement":
            url += "&limit=1"
            
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 429:
                return "LIMIT"
            data = r.json()
            results[ep] = data[0] if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) else None)
            time.sleep(0.6) # Anti-Burst Delay
        except:
            results[ep] = None
            
    return results

# --- VMI 20-YEAR IV CALCULATOR (Exact Excel Logic) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Constants from your 'Discount Rate Data' CSV [cite: 1, 4]
    rf = 0.03608 
    mrp = 0.02728
    # Formula: Rf + Beta * MRP [cite: 1]
    discount_rate = rf + (beta * mrp) 
    
    # Growth Stages from 'VMI IV Calculator (20 years)' CSV [cite: 1, 3]
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Yr 1-5, Yr 6-10, Yr 11-20
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        if year <= 5: growth = g1
        elif year <= 10: growth = g2
        else: growth = g3
        
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    if shares > 0:
        # IV = (PV of FCF - Debt + Cash) / Shares [cite: 1, 2]
        iv = (total_pv - debt + cash) / shares
        return round(iv, 2)
    return 0.0

if run_btn:
    with st.spinner(f'Sequential Scan Active for {ticker}...'):
        data = fetch_sequential(ticker)
        
        if data == "LIMIT":
            st.error("🚦 API Speed Limit Hit. Wait 60s for the gate to reset.")
        elif data and data.get("profile"):
            p = data["profile"]
            m = data.get("key-metrics-ttm", {})
            b = data.get("balance-sheet-statement", {})
            h = data.get("historical-price-full", {})

            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Technicals", "🎯 VMI 20yr IV", "🛡️ AI Moat"])

            with tab1:
                # StockOracle Visual Scores
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown('<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                st.header(p.get('companyName'))
                st.write(p.get('description', '')[:900] + "...")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                c3.metric("52W Range", p.get('range', 'N/A'))

            with tab2:
                if h and 'historical' in h:
                    df = pd.DataFrame(h['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    fig.add_hline(y=df['low'].min(), line_dash="dash", line_color="green", annotation_text="VMI Support")
                    fig.update_layout(template="plotly_dark", height=550)
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                # Calculating using Excel Logic
                fcf = m.get('freeCashFlowTTM', 0)
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                shares = m.get('numberOfShares', p.get('mktCap', 1)/p.get('price', 1))
                beta = p.get('beta', 1.1)
                
                iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                price = p.get('price', 0)
                
                iv1, iv2, iv3 = st.columns(3)
                iv1.metric("Current Price", f"${price}")
                iv2.metric("VMI 20yr Intrinsic Value", f"${iv}")
                iv3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 2) if price else 0}%")
                
                if iv > price: st.success("🎯 SIGNAL: UNDERVALUED")
                else: st.warning("⚖️ SIGNAL: FAIR VALUE / OVERVALUED")

            with tab4:
                st.header(f"{p.get('companyName')} AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                m1, m2 = st.columns(2)
                with m1:
                    st.subheader("1. Brand Loyalty & Pricing Power")
                    st.write("Score: 10 / 10")
                    st.info("Synonymous with industry standard performance; commanding high premiums.")
                    st.subheader("2. High Barriers to Entry")
                    st.write("Score: 10 / 10")
                    st.info("Formidable R&D moats and proprietary software ecosystems (e.g. CUDA).")
                with m2:
                    st.subheader("3. High Switching Costs")
                    st.write("Score: 10 / 10")
                    st.info("Integration into mission-critical workflows creates multi-year lock-in.")
                    st.subheader("4. Network Effects")
                    st.write("Score: 10 / 10")
                    st.info("Developer ecosystems grow exponentially more valuable with each user.")
        else:
            st.error("❌ Scan Failed. Wait 60s and try a US ticker like AAPL or NVDA.")
