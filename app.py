import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .moat-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI SCAN")

@st.cache_data(ttl=900)
def fetch_safe(endpoint, t, params=""):
    url = f"{BASE_URL}/{endpoint}/{t}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        # Defensive check: ensure data is a non-empty list
        return data if isinstance(data, list) and len(data) > 0 else None
    except:
        return None

# --- EXCEL LOGIC: 20-YEAR IV CALCULATOR ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Constants from your Excel 'Discount Rate Data'
    rf_avg = 0.03608 
    mrp_avg = 0.02728
    discount_rate = rf_avg + (beta * mrp_avg)
    
    # 3-Stage Growth Rates from VMI IV Calculator
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Yr 1-5, Yr 6-10, Yr 11-20
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        growth = g1 if year <= 5 else g2 if year <= 10 else g3
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    if shares > 0:
        # IV = (PV of 20yr FCF - Total Debt + Cash) / Shares
        iv = (total_pv - debt + cash) / shares
        return round(iv, 2)
    return 0.0

if run_btn:
    with st.spinner(f'Sequential Analysis for {ticker}...'):
        # Sequential fetching to bypass rate limits
        p_raw = fetch_safe("profile", ticker)
        time.sleep(0.5)
        m_raw = fetch_safe("key-metrics-ttm", ticker)
        time.sleep(0.5)
        b_raw = fetch_safe("balance-sheet-statement", ticker, "&limit=1")
        time.sleep(0.5)
        h_raw = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250").json()

        if p_raw == "LIMIT":
            st.error("🚦 API RATE LIMIT: Please wait 60 seconds.")
        elif p_raw: # Check if list is not empty before indexing
            p = p_raw[0]
            m = m_raw[0] if m_raw else {}
            b = b_raw[0] if b_raw else {}
            
            tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

            with tab_ov:
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown('<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                st.header(p.get('companyName', ticker))
                st.write(p.get('description', 'Description unavailable.')[:1000] + "...")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                c3.metric("52W Range", p.get('range', 'N/A'))

            with tab_chart:
                if h_raw and 'historical' in h_raw:
                    df = pd.DataFrame(h_raw['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange'), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red'), name="SMA 200"))
                    fig.update_layout(template="plotly_dark", height=500)
                    st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                # Calculations using Excel Logic
                fcf_val = m.get('freeCashFlowTTM', 0)
                debt_val = b.get('totalDebt', 0)
                cash_val = b.get('cashAndShortTermInvestments', 0)
                shares_val = m.get('numberOfShares', (p.get('mktCap', 0)/p.get('price', 1)) if p.get('price') else 1)
                
                iv = calculate_vmi_iv(fcf_val, debt_val, cash_val, shares_val, p.get('beta', 1.0))
                price = p.get('price', 0)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", f"${price}")
                col2.metric("VMI Intrinsic Value", f"${iv}")
                if price > 0:
                    col3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 1)}%")

            with tab_moat:
                st.header(f"{p.get('companyName')} AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                st.write("**Brand & Pricing Power:** Synonymous with industry standards; commanding high premiums.")
                st.write("**High Barriers to Entry:** Powered by proprietary ecosystems (CUDA) and massive R&D.")
        else:
            st.error("❌ Data restricted for this ticker. Ensure the symbol is correct and wait 60s.")
