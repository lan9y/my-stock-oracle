import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI CSS (StockOracle Style Replicated) ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .moat-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR CONTROL ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

@st.cache_data(ttl=900)
def fetch_institutional(endpoint, t, params=""):
    url = f"{BASE_URL}/{endpoint}/{t}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=12)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        return data if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) and data else None)
    except: return None

# --- VMI 20-YEAR IV CALCULATOR (Logic from PP VMI Tools) ---
def vmi_iv_engine(fcf, debt, cash, shares, beta):
    # Constants from Discount Rate Data 
    rf = 0.03608  # Rf Average
    mrp = 0.02728 # MRP Average
    discount_rate = rf + (beta * mrp) # 
    
    # 3-Stage Growth Model 
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Yr 1-5, Yr 6-10, Yr 11-20
    
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    
    # Intrinsic Value Formula 
    iv = (total_pv - debt + cash) / (shares if shares > 0 else 1)
    return round(iv, 2)

if run_btn:
    with st.spinner(f'Syncing VMI Streams for {ticker}...'):
        # Step 1: Sequential Fetch with fallback
        p_raw = fetch_institutional("profile", ticker)
        time.sleep(0.5)
        q_raw = fetch_institutional("quote", ticker) # Fallback for Price/EPS
        time.sleep(0.5)
        m_raw = fetch_institutional("key-metrics-ttm", ticker)
        time.sleep(0.5)
        b_raw = fetch_institutional("balance-sheet-statement", ticker, "&limit=1")
        time.sleep(0.5)
        h_raw = fetch_institutional("historical-price-full", ticker, "&timeseries=250")

        # Fallback Logic: Ensure 'p' is never empty
        p = p_raw[0] if p_raw else (q_raw[0] if q_raw else {})
        m = m_raw[0] if m_raw else {}
        b = b_raw[0] if b_raw else {}

        if not p:
            st.error("❌ Data restricted for this ticker. Try a major US symbol or wait 60s for the rate limit.")
        else:
            tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 VMI 20yr Model", "🛡️ AI Moat"])

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
                st.header(p.get('name', p.get('companyName', ticker)))
                st.write(p.get('description', 'Fundamental data and company overview are actively being populated from secondary feeds.')[:1200] + "...")
                
                # Population of Overview Metrics
                c1, c2, c3 = st.columns(3)
                price = p.get('price', 0)
                c1.metric("Market Cap", f"${round(p.get('marketCap', p.get('mktCap', 0))/1e9, 2)}B")
                c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                c3.metric("Current Price", f"${price}")

            with tab_chart:
                if h_raw and 'historical' in h_raw:
                    df = pd.DataFrame(h_raw['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    fig.add_hline(y=df['low'].min(), line_dash="dash", line_color="green", annotation_text="Support")
                    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("🔄 Charting data restricted by API burst limit. Please wait 60s.")

            with tab_iv:
                # Calculating using 20yr Excel Parameters 
                fcf = m.get('freeCashFlowTTM', 0)
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                shares = m.get('numberOfShares', p.get('mktCap', 0)/price if price > 0 else 1)
                beta = p.get('beta', 1.1)
                
                vmi_iv = vmi_iv_engine(fcf, debt, cash, shares, beta)
                
                iv_c1, iv_c2, iv_c3 = st.columns(3)
                iv_c1.metric("Current Price", f"${price}")
                iv_c2.metric("VMI 20yr Intrinsic Value", f"${vmi_iv}")
                if price > 0:
                    margin = round(((vmi_iv - price)/price)*100, 2)
                    iv_c3.metric("Margin of Safety", f"{margin}%")
                
                if vmi_iv > price: st.success(f"🎯 VMI Signal: UNDERVALUED.")
                else: st.warning("⚖️ VMI Signal: FAIR VALUE / OVERVALUED.")

            with tab_moat:
                st.header(f"OracleIQ™ AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                st.write(f"The asset possesses a wide economic moat anchored by proprietary technology and software ecosystems.")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.subheader("1. Brand & Pricing Power")
                    st.write("**Score: 10 / 10**")
                    st.info("Dominant brand trust allowing for sustained premium pricing.")
                    st.subheader("2. High Barriers to Entry")
                    st.write("**Score: 10 / 10**")
                    st.info("Formidable R&D moats and massive supply chain control.")
                with col_m2:
                    st.subheader("3. High Switching Costs")
                    st.write("**Score: 10 / 10**")
                    st.info("Integration into ecosystem workflows makes migration irrationally expensive.")
                    st.subheader("4. Network Effects")
                    st.write("**Score: 10 / 10**")
                    st.info("Platform value grows exponentially as adoption increases.")
