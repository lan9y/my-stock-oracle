import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI CSS (StockOracle Styles) ---
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

# --- SIDEBAR CONTROL ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

@st.cache_data(ttl=3600)
def fetch_data(endpoint, ticker_val, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker_val}?apikey={API_KEY}{params}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 429: return "LIMIT"
        data = response.json()
        return data if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) else None)
    except: return None

# --- VMI 20-YEAR IV CALCULATOR (EXACT EXCEL LOGIC) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Parameters from 'Discount Rate Data.csv' [cite: 4]
    rf = 0.03608  # Risk Free Rate Average
    mrp = 0.02728 # Market Risk Premium Average
    
    # Formula: Discount Rate = Risk Free Rate + Beta * Market Risk Premium 
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages from 'VMI IV Calculator (20 years).csv' 
    g1 = 0.1748 # Yr 1-5 [cite: 2]
    g2 = 0.15   # Yr 6-10 [cite: 2, 3]
    g3 = 0.04   # Yr 11-20 [cite: 1, 3]
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        growth = g1 if year <= 5 else g2 if year <= 10 else g3
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    # Intrinsic Value Formula: (PV of 20yr FCF - Debt + Cash) / Shares 
    iv = (total_pv - debt + cash) / shares if shares > 0 else 0
    return round(iv, 2)

if run_btn:
    with st.spinner(f'Polite VMI Sync Active for {ticker} (Wait for reset)...'):
        # WE PACE OUT REQUESTS BY 2 SECONDS TO STAY UNDER THE FREE TIER RADAR
        p_res = fetch_data("profile", ticker)
        time.sleep(2.0)
        m_res = fetch_data("key-metrics-ttm", ticker)
        time.sleep(2.0)
        b_res = fetch_data("balance-sheet-statement", ticker, "&limit=1")
        time.sleep(2.0)
        h_res = fetch_data("historical-price-full", ticker, "&timeseries=250")

        # DEFENSIVE DATA CHECKING
        if p_res == "LIMIT":
            st.error("🚦 API Speed Limit Hit. This is a temporary lock. Please wait exactly 60s and try again.")
        elif p_res:
            p = p_res[0] if isinstance(p_res, list) else {}
            m = m_res[0] if m_res and isinstance(m_res, list) else {}
            b = b_res[0] if b_res and isinstance(b_res, list) else {}
            
            tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

            with tab_ov:
                # SCORECARDS (Visual from StockOracle Screenshot)
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown('<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                st.header(p.get('companyName', ticker))
                st.write(p.get('description', 'Fundamental data overview.')[:1000] + "...")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                c3.metric("52W Range", p.get('range', 'N/A'))

            with tab_chart:
                if h_res and 'historical' in h_res:
                    df = pd.DataFrame(h_res['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    
                    vmi_support = df['low'].min()
                    fig.add_hline(y=vmi_support, line_dash="dash", line_color="green", annotation_text="Key Support")
                    
                    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Technical data currently loading or blocked by API speed limits.")

            with tab_iv:
                # Calculate using Excel Parameters
                fcf = m.get('freeCashFlowTTM', 0)
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                price = p.get('price', 1)
                shares = m.get('numberOfShares', (p.get('mktCap', 0)/price if price > 0 else 0))
                beta = p.get('beta', 1.1)
                
                vmi_iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                
                iv1, iv2, iv3 = st.columns(3)
                iv1.metric("Current Price", f"${price}")
                iv2.metric("VMI 20yr IV", f"${vmi_iv}")
                if price > 0:
                    margin = round(((vmi_iv - price) / price) * 100, 2)
                    iv3.metric("Margin of Safety", f"{margin}%", delta=f"{margin}%")
                
                if vmi_iv > price: st.success("🎯 SIGNAL: UNDERVALUED (VMI Buy Zone)")
                else: st.warning("⚖️ SIGNAL: FAIR VALUE / OVERVALUED")

            with tab_moat:
                st.header("OracleIQ™ AI Moat Analysis (NVDA Focus)")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                st.markdown("""
                **1. Brand Loyalty & Pricing Power (10/10)**: Dominant standard in AI/Gaming; high price premiums.  
                **2. High Barriers to Entry (10/10)**: CUDA software ecosystem and $7B+ annual R&D moat.  
                **3. High Switching Costs (10/10)**: Multi-year lock-in due to integrated hardware/software stack.  
                **4. Network Effect (10/10)**: Millions of active users; library of optimized AI applications.  
                **5. Economies of Scale (10/10)**: Cost leadership through massive supply chain control.
                """)
        else:
            st.error("❌ Data restricted or symbol not found. Wait 60s.")
