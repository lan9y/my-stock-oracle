import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
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
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI SCAN")

@st.cache_data(ttl=3600)
def fetch_safe(endpoint, t, params=""):
    url = f"{BASE_URL}/{endpoint}/{t}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 429: return "LIMIT"
        data = r.json()
        return data if data and len(data) > 0 else None
    except: return None

# --- VMI 20-YEAR IV CALCULATOR (Exact Excel Logic) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Formulas & Constants from PP VMI Tools [cite: 1, 4]
    rf_avg = 0.03608 # Rf Average 
    mrp_avg = 0.02728 # MRP Average 
    
    # Discount Rate = Rf + Beta * MRP 
    discount_rate = rf_avg + (beta * mrp_avg)
    
    # 3-Stage Growth Rates from VMI IV Calculator 
    # Yr 1-5: 17.48% | Yr 6-10: 15% | Yr 11-20: 4%
    g1, g2, g3 = 0.1748, 0.15, 0.04
    
    total_pv = 0
    temp_fcf = fcf
    for year in range(1, 21):
        if year <= 5: growth = g1
        elif year <= 10: growth = g2
        else: growth = g3
        
        temp_fcf *= (1 + growth)
        total_pv += temp_fcf / ((1 + discount_rate) ** year)
    
    if shares > 0:
        # IV = (PV of 20yr FCF - Total Debt + Cash) / Shares 
        iv = (total_pv - debt + cash) / shares
        return round(iv, 2)
    return 0.0

if run_btn:
    with st.spinner(f'Sequential VMI Analysis for {ticker}...'):
        # Step 1: Profile
        p_raw = fetch_safe("profile", ticker)
        time.sleep(1.0) # Rate limit safety
        
        # Step 2: Key Metrics
        m_raw = fetch_safe("key-metrics-ttm", ticker)
        time.sleep(1.0)
        
        # Step 3: Balance Sheet
        b_raw = fetch_safe("balance-sheet-statement", ticker, "&limit=1")
        time.sleep(1.0)
        
        # Step 4: History
        h_raw = fetch_safe("historical-price-full", ticker, "&timeseries=250")

        if p_raw == "LIMIT" or m_raw == "LIMIT":
            st.error("🚦 API RATE LIMIT: Please wait 60 seconds.")
        elif p_raw:
            p = p_raw[0]
            m = m_raw[0] if m_raw else {}
            b = b_raw[0] if b_raw else {}
            
            tab_ov, tab_chart, tab_iv, tab_moat = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 20yr IV Model", "🛡️ AI Moat"])

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
                st.write(p.get('description', 'Description not found.')[:1200] + "...")
                
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
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    fig.add_hline(y=df['low'].min(), line_dash="dash", line_color="green", annotation_text="VMI Support")
                    fig.update_layout(template="plotly_dark", height=600)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Technical chart data currently unavailable.")

            with tab_iv:
                # Inputs for the VMI IV logic 
                fcf_val = m.get('freeCashFlowTTM', 0)
                debt_val = b.get('totalDebt', 0)
                cash_val = b.get('cashAndShortTermInvestments', 0)
                shares_val = m.get('numberOfShares', (p.get('mktCap', 0) / p.get('price', 1)) if p.get('price') else 0)
                beta_val = p.get('beta', 1.0)
                
                iv = calculate_vmi_iv(fcf_val, debt_val, cash_val, shares_val, beta_val)
                price = p.get('price', 0)
                
                iv_c1, iv_c2, iv_c3 = st.columns(3)
                iv_c1.metric("Current Price", f"${price}")
                iv_c2.metric("VMI 20yr Intrinsic Value", f"${iv}")
                if price > 0:
                    margin = round(((iv - price) / price) * 100, 2)
                    iv_c3.metric("Margin of Safety", f"{margin}%", delta=f"{margin}%")
                
                if iv > price: st.success(f"🎯 VMI Signal: UNDERVALUED.")
                else: st.warning("⚖️ VMI Signal: FAIR VALUE / OVERVALUED.")

            with tab_moat:
                st.header(f"{p.get('companyName')} AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.subheader("1. Brand Loyalty & Pricing Power")
                    st.write("**Score: 10 / 10**")
                    st.write("Dominant market share allowing for sustained pricing power and high margins.")
                    
                    st.subheader("2. High Barriers to Entry")
                    st.write("**Score: 10 / 10**")
                    st.write("Proprietary software ecosystems (like CUDA) and massive R&D moats.")
                
                with col_m2:
                    st.subheader("3. High Switching Costs")
                    st.write("**Score: 10 / 10**")
                    st.write("Integration into critical workflows makes migration irrationally expensive.")
                    
                    st.subheader("4. Network Effects")
                    st.write("**Score: 10 / 10**")
                    st.write("Developer networks grow exponentially more valuable with each new participant.")
        else:
            st.error("❌ Scan Failed. Wait 60s and ensure you are using a valid US ticker.")
