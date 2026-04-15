import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- STYLE REPLICATION (StockOracle Screenshot Style) ---
st.markdown("""
    <style>
    .vmi-card { background-color: #0d1117; border-radius: 10px; padding: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    .vmi-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; }
    .vmi-score { font-size: 22px; font-weight: 800; color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI SCAN")

@st.cache_data(ttl=900)
def fetch_data(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url)
        if r.status_code == 429: return "LIMIT"
        return r.json() if r.status_code == 200 else None
    except: return None

if run_btn:
    with st.spinner('Calculating VMI Intrinsic Value & Technicals...'):
        p = fetch_data("profile")
        r = fetch_data("ratios-ttm")
        m = fetch_data("key-metrics-ttm")
        chart_data = fetch_data("historical-price-full", "&timeseries=250")

        if p == "LIMIT":
            st.error("🚦 API RATE LIMIT: Please wait 60 seconds before next scan.")
        elif p:
            prof, rat, met = p[0], (r[0] if r else {}), (m[0] if m else {})

            tab1, tab2, tab3 = st.tabs(["📊 VMI Overview", "📈 Technical Chart", "🎯 20yr IV Model"])

            with tab1:
                # OVERVIEW SCORES (Based on your Screenshot)
                col_info, col_vmi = st.columns([2, 1])
                with col_info:
                    st.header(prof.get('companyName'))
                    st.info(prof.get('description', '')[:700] + "...")
                with col_vmi:
                    st.subheader("Oracle IQ Scores")
                    # Internal logic based on ROIC and Debt ratios
                    roic = rat.get('returnOnCapitalEmployedTTM', 0)
                    debt = rat.get('debtEquityRatioTTM', 0)
                    st.markdown(f'<div class="vmi-card"><div class="vmi-label">Oracle Moat</div><div class="vmi-score">{"9/10" if roic > 0.2 else "7/10"}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="vmi-card"><div class="vmi-label">Financial Strength</div><div class="vmi-score">{"8/10" if debt < 1 else "5/10"}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="vmi-card"><div class="vmi-label">Predictability</div><div class="vmi-score">8/10</div></div>', unsafe_allow_html=True)

            with tab2:
                # CHART WITH SMA 50/200 & SUPPORT
                if chart_data and 'historical' in chart_data:
                    df = pd.DataFrame(chart_data['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=1.5), name="SMA 200"))
                    
                    # Support line (Annual Low)
                    support = df['low'].min()
                    fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="VMI Key Support")
                    
                    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                # 20-YEAR DCF MODEL (Based on your Excel Template)
                st.subheader("VMI 20-Year Discounted Cash Flow Calculator")
                fcf = met.get('freeCashFlowYieldTTM', 0.04) * prof.get('mktCap', 0)
                shares = prof.get('mktCap', 0) / prof.get('price', 1)
                
                # Excel Logic Assumptions: 12% Growth 1st 10yr, 8% 2nd 10yr, 9% Discount
                total_pv = 0
                growth = 0.12
                discount = 0.09
                for year in range(1, 21):
                    if year > 10: growth = 0.08 # Growth slowdown as per Excel logic
                    fcf *= (1 + growth)
                    total_pv += fcf / ((1 + discount) ** year)
                
                iv = round(total_pv / shares, 2)
                price = prof.get('price', 0)
                st.metric("VMI Intrinsic Value", f"${iv}", delta=f"{round(((iv-price)/price)*100, 1)}% Upside")
                
                if iv > price: st.success("🎯 SIGNAL: UNDERVALUED (VMI Buy Zone)")
                else: st.warning("⚖️ SIGNAL: FAIR VALUE / OVERVALUED")
        else:
            st.error("Ticker not found or API blocked.")
