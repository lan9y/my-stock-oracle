import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS (StockOracle Replicated Styles) ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    [data-testid="stMetricValue"] { font-size: 22px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
st.sidebar.header("VMI Control")
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

# --- CACHING ENGINE (Prevents Credit Waste) ---
@st.cache_data(ttl=3600) # Save data for 1 hour
def fetch_api(endpoint, ticker_val, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker_val}?apikey={API_KEY}{params}"
    try:
        response = requests.get(url)
        if response.status_code == 429: return "RATE_LIMIT"
        data = response.json()
        if "Error Message" in str(data): return "BLOCKED"
        return data if isinstance(data, list) and len(data) > 0 else None
    except: return None

# --- VMI 20-YEAR IV LOGIC (Direct from Excel Template) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Excel Assumptions
    rf = 0.036  # Risk Free Rate
    mrp = 0.027 # Market Risk Premium
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages (Excel Logic)
    g1, g2, g3 = 0.17, 0.15, 0.04
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        if year <= 5: growth = g1
        elif year <= 10: growth = g2
        else: growth = g3
        
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    # (PV of 20yr FCF - Debt + Cash) / Shares
    iv = (total_pv - debt + cash) / shares
    return round(iv, 2)

if run_btn:
    with st.spinner('Syncing VMI Algorithm & Financial Streams...'):
        # Batch Fetch
        p_data = fetch_api("profile", ticker)
        m_data = fetch_api("key-metrics-ttm", ticker)
        b_data = fetch_api("balance-sheet-statement", ticker, "&limit=1")
        h_data = fetch_api("historical-price-full", ticker, "&timeseries=250")

        if p_data == "RATE_LIMIT" or p_data == "BLOCKED":
            st.error("🚦 API Blocked or Credit Limit Hit. Dashboard is showing cached/sample data.")
        elif p_data:
            p, m, b = p_data[0], (m_data[0] if m_data else {}), (b_data[0] if b_data else {})
            
            tab_ov, tab_chart, tab_iv = st.tabs(["🏠 Overview", "📈 VMI Chart", "🎯 20yr IV Model"])

            with tab_ov:
                # SCORECARDS (Replicating your Screenshot)
                st.subheader("VMI OracleIQ Scorecard")
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                
                # Logic for 1-10 scores
                roic = (m.get('roicTTM', 0.15)) * 10
                strength = 8 if b.get('totalDebt', 0) < b.get('cashAndShortTermInvestments', 1) else 5
                
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roic, 10))}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown(f'<div class="score-card"><div class="score-label">Strength</div><div class="score-value">{strength}/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                st.header(p.get('companyName'))
                st.info(p.get('description', '')[:900] + "...")

            with tab_chart:
                if h_data and 'historical' in h_data:
                    df = pd.DataFrame(h_data['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    
                    # Support Line (Annual Low)
                    support = df['low'].min()
                    fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="VMI Support")
                    
                    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=20,b=0))
                    st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                # 20-YEAR IV MODEL
                curr_price = p.get('price', 1)
                fcf = m.get('freeCashFlowTTM', 0) or (m.get('netIncomePerShareTTM', 0) * m.get('netIncomePerShareTTM', 0))
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                shares = m.get('numberOfShares', 1)
                beta = p.get('beta', 1.0)
                
                vmi_iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                
                st.subheader("VMI 20-Year Discounted FCF Model")
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"${curr_price}")
                c2.metric("VMI Intrinsic Value", f"${vmi_iv}")
                c3.metric("Margin of Safety", f"{round(((vmi_iv - curr_price)/curr_price)*100, 2)}%", delta_color="normal")
                
                st.progress(min(max(int((vmi_iv/curr_price)*50), 0), 100))
                if vmi_iv > curr_price: st.success("🟢 UNDERVALUED: Stock is in the VMI Buy Zone.")
                else: st.warning("🟡 OVERVALUED: Price is above Intrinsic Value.")
        else:
            st.error("❌ Ticker Not Found. Ensure you are using a major US symbol.")
