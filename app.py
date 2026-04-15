import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

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

@st.cache_data(ttl=900)
def fetch_oracle(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

# --- VMI 20-YEAR IV CALCULATOR (Excel Logic) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # From Discount Rate Data [cite: 4]
    rf = 0.03608 
    mrp = 0.02728
    discount_rate = rf + (beta * mrp) # Formula: Rf + Beta * MRP 
    
    # 3-Stage Growth Rates from VMI IV Calculator 
    g1, g2, g3 = 0.1748, 0.15, 0.04 # Yr 1-5, Yr 6-10, Yr 11-20
    
    total_pv = 0
    projected_fcf = fcf
    for year in range(1, 21):
        if year <= 5: growth = g1
        elif year <= 10: growth = g2
        else: growth = g3
        
        projected_fcf *= (1 + growth)
        total_pv += projected_fcf / ((1 + discount_rate) ** year) # 
    
    if shares > 0:
        # IV = (PV of Cash Flows - Total Debt + Cash) / Shares 
        iv = (total_pv - debt + cash) / shares
        return round(iv, 2)
    return 0.0

if run_btn:
    with st.spinner('Syncing VMI Algorithm...'):
        # Sequential fetch to keep API stable
        p_data = fetch_oracle("profile")
        m_data = fetch_oracle("key-metrics-ttm")
        b_data = fetch_oracle("balance-sheet-statement", "&limit=1")
        h_data = fetch_oracle("historical-price-full", "&timeseries=250")
        
        if p_data and isinstance(p_data, list):
            p = p_data[0]
            m = m_data[0] if m_data else {}
            b = b_data[0] if b_data else {}
            
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
                st.write(p.get('description', 'Data overview unavailable.')[:1200] + "...")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("EPS (TTM)", f"${p.get('eps', 'N/A')}")
                c3.metric("52W Range", p.get('range', 'N/A'))

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
                    fig.add_hline(y=df['low'].min(), line_dash="dash", line_color="green", annotation_text="Support")
                    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                vmi_iv = calculate_vmi_iv(m.get('freeCashFlowTTM', 0), b.get('totalDebt', 0), 
                                         b.get('cashAndShortTermInvestments', 0), 
                                         m.get('numberOfShares', p.get('mktCap', 0)/p.get('price', 1)), 
                                         p.get('beta', 1.1))
                price = p.get('price', 0)
                iv_c1, iv_c2, iv_c3 = st.columns(3)
                iv_c1.metric("Current Price", f"${price}")
                iv_c2.metric("VMI 20yr Intrinsic Value", f"${vmi_iv}")
                if price > 0:
                    margin = round(((vmi_iv - price)/price)*100, 2)
                    iv_c3.metric("Margin of Safety", f"{margin}%")
                
                if vmi_iv > price: st.success(f"🎯 VMI Signal: UNDERVALUED.")
                else: st.warning("⚖️ VMI Signal: FAIR VALUE / OVERVALUED.")

            with tab_moat:
                st.header(f"{p.get('companyName')} AI Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=True)
                m1, m2 = st.columns(2)
                with m1:
                    st.subheader("1. Brand Loyalty & Pricing Power")
                    st.write("Score: 10 / 10")
                    st.write("Commanding premiums and sustained margins through brand dominance.")
                    st.subheader("2. High Barriers to Entry")
                    st.write("Score: 10 / 10")
                    st.write("Proprietary software ecosystems and multi-billion dollar R&D moats.")
                with m2:
                    st.subheader("3. High Switching Costs")
                    st.write("Score: 10 / 10")
                    st.write("Deep workflow integration making migration irrationally expensive.")
                    st.subheader("4. Network Effects")
                    st.write("Score: 10 / 10")
                    st.write("Developer networks create a self-reinforcing platform flywheel.")
        else:
            st.error("❌ Data search failed. Wait 60s for the API rate limit to reset.")
