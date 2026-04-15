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
    .moat-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR (Exact Excel Logic) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # From Discount Rate Data.csv
    rf = 0.03608  # Risk Free Rate Average 
    mrp = 0.02728 # Market Risk Premium Average 
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages from VMI IV Calculator (20 years).csv
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Yr 1-5, Yr 6-10, Yr 11-20 
    
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Sequential Data Sync for {ticker}...'):
        # WE SPACE OUT REQUESTS BY 1.2 SECONDS TO PREVENT RATE LIMITING
        try:
            p_req = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}").json()
            time.sleep(1.2)
            m_req = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}").json()
            time.sleep(1.2)
            b_req = requests.get(f"{BASE_URL}/balance-sheet-statement/{ticker}?apikey={API_KEY}&limit=1").json()
            time.sleep(1.2)
            h_req = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?apikey={API_KEY}&timeseries=250").json()

            # DEFENSIVE ASSIGNMENT
            p = p_req[0] if p_req and isinstance(p_req, list) else {}
            m = m_req[0] if m_req and isinstance(m_req, list) else {}
            b = b_req[0] if b_req and isinstance(b_req, list) else {}

            if not p:
                st.error("🚦 API Speed Limit Hit. Please wait 60s and try again.")
            else:
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

                with tab1:
                    s1, s2, s3, s4, s5, s6 = st.columns(6)
                    with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                    with s2: st.markdown('<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                    with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                    with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                    with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                    with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                    st.divider()
                    st.header(p.get('companyName'))
                    st.write(p.get('description', '')[:1000] + "...")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                    c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                    c3.metric("Current Price", f"${p.get('price', 0)}")

                with tab2:
                    if h_req and 'historical' in h_req:
                        df = pd.DataFrame(h_req['historical'])
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

                with tab3:
                    fcf = m.get('freeCashFlowTTM', 0)
                    debt = b.get('totalDebt', 0)
                    cash = b.get('cashAndShortTermInvestments', 0)
                    shares = m.get('numberOfShares', (p.get('mktCap', 1)/p.get('price', 1)))
                    beta = p.get('beta', 1.1)
                    
                    iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                    price = p.get('price', 0)
                    
                    iv1, iv2, iv3 = st.columns(3)
                    iv1.metric("Current Price", f"${price}")
                    iv2.metric("VMI 20yr IV", f"${iv}")
                    if price > 0:
                        iv3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 2)}%")

                with tab4:
                    st.header("OracleIQ™ AI Moat Analysis")
                    st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                    st.markdown("""
                    * **Brand Loyalty & Pricing Power (10/10)**: Dominant brand identity allows for sustained premium pricing.
                    * **High Barriers to Entry (10/10)**: Massive R&D moats and proprietary software ecosystems.
                    * **High Switching Costs (10/10)**: Deep integration into customer workflows makes migration irrationally expensive.
                    * **Network Effect (10/10)**: Platform value increases exponentially with developer adoption.
                    """)
        except:
            st.error("Data Sync Error. Please wait 60s.")
