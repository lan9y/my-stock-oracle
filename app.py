import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
# Using v3 for consistency with your metrics
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
def fetch_oracle(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data if isinstance(data, list) and len(data) > 0 else None
    except: return None

# --- EXCEL LOGIC: 20-YEAR IV CALCULATOR ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # From Discount Rate Data
    rf = 0.03608 
    mrp = 0.02728
    discount_rate = rf + (beta * mrp)
    
    # Growth Stages from VMI IV Calculator (20 years)
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
    
    # (PV of 20yr FCF - Debt + Cash) / Shares
    iv = (total_pv - debt + cash) / (shares if shares > 0 else 1)
    return round(iv, 2)

if run_btn:
    with st.spinner('Syncing VMI Algorithm...'):
        # Batch Fetch with sequential checks
        p_data = fetch_oracle("profile")
        m_data = fetch_oracle("key-metrics-ttm")
        b_data = fetch_oracle("balance-sheet-statement", "&limit=1")
        h_data = fetch_oracle("historical-price-full", "&timeseries=250")
        
        if p_data:
            p, m, b = p_data[0], (m_data[0] if m_data else {}), (b_data[0] if b_data else {})
            
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
                st.header(p.get('companyName'))
                st.write(p.get('description', 'No summary available.')[:1000] + "...")
                
                st.subheader("Current Trading Context")
                c1, c2, c3 = st.columns(3)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("P/E Ratio", round(p.get('price', 0)/p.get('eps', 1), 2) if p.get('eps') else "N/A")
                c3.metric("52W Range", f"{p.get('range', 'N/A')}")

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
                    
                    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Technical data unavailable. API rate limit may have been reached.")

            with tab_iv:
                # IV Inputs from excel logic
                fcf = m.get('freeCashFlowTTM', 0)
                debt = b.get('totalDebt', 0)
                cash = b.get('cashAndShortTermInvestments', 0)
                shares = m.get('numberOfShares', 1)
                beta = p.get('beta', 1.1)
                
                vmi_iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                price = p.get('price', 0)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"${price}")
                c2.metric("VMI 20yr Intrinsic Value", f"${vmi_iv}")
                c3.metric("Margin of Safety", f"{round(((vmi_iv - price)/price)*100, 2) if price > 0 else 0}%")
                
                if vmi_iv > price:
                    st.success(f"🎯 VMI Signal: UNDERVALUED. Buy Zone established at ${vmi_iv}.")
                else:
                    st.warning("⚖️ VMI Signal: FAIR VALUE / OVERVALUED.")

            with tab_moat:
                st.header(f"{p.get('companyName')} Moat Analysis")
                st.markdown('<div class="moat-box"><h3>Wide Moat</h3><p>Overall score: 10 / 10</p></div>', unsafe_allow_html=
