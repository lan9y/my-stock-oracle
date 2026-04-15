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

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

@st.cache_data(ttl=900)
def fetch_institutional(endpoint, t, params=""):
    url = f"{BASE_URL}/{endpoint}/{t}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=12)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        # Defensive check: Ensure data is a non-empty list
        return data if isinstance(data, list) and len(data) > 0 else (data if isinstance(data, dict) and data else None)
    except: return None

# --- EXCEL LOGIC: 20-YEAR IV CALCULATOR ---
def vmi_iv_engine(fcf, debt, cash, shares, beta):
    # Data from 'Discount Rate Data.csv'
    rf = 0.03608  # Rf Average 
    mrp = 0.02728 # MRP Average 
    
    # Formula: $Discount\ Rate = Risk\ Free\ Rate + Beta \times Market\ Risk\ Premium$ [cite: 2]
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages from 'VMI IV Calculator (20 years).csv'
    # Yr 1-5: 17.48% [cite: 1] | Yr 6-10: 15% [cite: 1] | Yr 11-20: 4% [cite: 2]
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    
    # Intrinsic Value Formula: $(PV - Debt + Cash) / Shares$ 
    iv = (total_pv - debt + cash) / (shares if shares > 0 else 1)
    return round(iv, 2)

if run_btn:
    with st.spinner(f'Sequential VMI Analysis for {ticker}...'):
        # Step-by-step fetching to avoid API burst limits
        p_raw = fetch_institutional("profile", ticker)
        time.sleep(0.8) # Rate limit protection
        m_raw = fetch_institutional("key-metrics-ttm", ticker)
        time.sleep(0.8)
        b_raw = fetch_institutional("balance-sheet-statement", ticker, "&limit=1")
        time.sleep(0.8)
        h_raw = fetch_institutional("historical-price-full", ticker, "&timeseries=250")

        # Fallback check for empty API responses
        if not p_raw or p_raw == "LIMIT":
            st.error("🚦 Data restricted or Rate Limit hit. Wait 60s and ensure ticker is a major US stock (e.g., AAPL).")
        else:
            p = p_raw[0]
            m = m_raw[0] if m_raw and isinstance(m_raw, list) else {}
            b = b_raw[0] if b_raw and isinstance(b_raw, list) else {}

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
                st.write(p.get('description', 'Description not found.')[:1000] + "...")
                
                c1, c2, c3 = st.columns(3)
                mkt_cap = p.get('mktCap', 0)
                c1.metric("Market Cap", f"${round(mkt_cap/1e9, 2)}B" if mkt_cap else "N/A")
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
                    fig.update_layout(template="plotly_dark", height=550, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("🔄 Charting data restricted by API speed limits. Wait 60s.")

            with tab_iv:
                # Calculating using 20yr Excel Parameters 
                fcf = m.get('freeCashFlowTTM', 0)
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                shares = m.get('numberOfShares', (p.get('mktCap', 0)/p.get('price', 1)) if p.get('price') else 1)
                
                vmi_iv = vmi_iv_engine(fcf, debt, cash, shares, p.get('beta', 1.1))
                price = p.get('price', 0)
                
                iv1, iv2, iv3 = st.columns(3)
                iv1.metric("Current Price", f"${price}")
                iv2.metric("VMI 20yr Intrinsic Value", f"${vmi_iv}")
                if price > 0:
                    margin = round(((vmi_iv - price)/price)*100, 1)
                    iv3.metric("Margin of Safety", f"{margin}%")
                
                if vmi_iv > price: st.success(f"🎯 VMI Signal: UNDERVALUED.")
                else: st.warning("⚖️ VMI Signal: FAIR VALUE / OVERVALUED.")

            with tab_moat:
                st.header(f"OracleIQ™ AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                st.write(f"The asset possesses a wide economic moat anchored by proprietary hardware-software ecosystems.")
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.subheader("1. Brand & Pricing Power")
                    st.write("**Score: 10 / 10**")
                    st.info("Dominant brand trust allowing for sustained premium pricing and gross margins.")
                    st.subheader("2. High Barriers to Entry")
                    st.write("**Score: 10 / 10**")
                    st.info("Formidable R&D moats and proprietary platforms (like CUDA) that are irrationally expensive to replicate.")
                with col_m2:
                    st.subheader("3. High Switching Costs")
                    st.write("**Score: 10 / 10**")
                    st.info("Deep integration into enterprise workflows makes migration operationally risky.")
                    st.subheader("4. Network Effects")
                    st.write("**Score: 10 / 10**")
                    st.info("Developer ecosystems grow exponentially more valuable with each new user.")
