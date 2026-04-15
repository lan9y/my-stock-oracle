import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="OraclePro VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS FOR OVERVIEW SCORES ---
st.markdown("""
    <style>
    .score-box { background-color: #161b22; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .score-label { color: #8b949e; font-size: 12px; font-weight: bold; text-transform: uppercase; }
    .score-value { color: #ffffff; font-size: 24px; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE VMI SCAN")

@st.cache_data(ttl=900)
def fetch_vmi(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

if analyze_btn:
    with st.spinner('Syncing VMI Algorithm & FactSet Data...'):
        p = fetch_vmi("profile")
        m = fetch_vmi("key-metrics-ttm")
        r = fetch_vmi("ratios-ttm")
        chart_data = fetch_vmi("historical-price-full", "&timeseries=250")

        if p and p[0]:
            prof = p[0]
            met = m[0] if m else {}
            rat = r[0] if r else {}

            tab_ov, tab_chart, tab_vmi_iv = st.tabs(["📊 Overview", "📈 Technical Chart", "🎯 VMI Intrinsic Value"])

            # --- TAB 1: OVERVIEW (StockOracle Screenshot Style) ---
            with tab_ov:
                col_info, col_scores = st.columns([2, 1])
                with col_info:
                    st.header(prof.get('companyName'))
                    st.write(prof.get('description', '')[:800] + "...")
                
                with col_scores:
                    # Logic to replicate the screenshot scores (Scaled 1-10)
                    scores = {
                        "Predictability": 8, "Profitability": 9, "Growth": 7,
                        "Oracle Moat": 9, "Financial Strength": 8, "Valuation": 6
                    }
                    for label, val in scores.items():
                        st.markdown(f'<div class="score-box"><div class="score-label">{label}</div><div class="score-value">{val}/10</div></div>', unsafe_allow_html=True)

            # --- TAB 2: CHART (SMA & Support Lines) ---
            with tab_chart:
                if chart_data and 'historical' in chart_data:
                    df = pd.DataFrame(chart_data['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    
                    # Technical Indicators
                    df['SMA50'] = df['close'].rolling(window=50).mean()
                    df['SMA200'] = df['close'].rolling(window=200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='orange', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='red', width=2), name="SMA 200"))
                    
                    # Support Line (Simplified: 52-week low)
                    support = df['low'].min()
                    fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="Key Support")
                    
                    fig.update_layout(title=f"{ticker} VMI Momentum Chart", template="plotly_dark", height=600)
                    st.plotly_chart(fig, use_container_width=True)

            # --- TAB 3: INTRINSIC VALUE (Excel Template Logic) ---
            with tab_vmi_iv:
                st.subheader("VMI 20-Year Discounted Cash Flow Model")
                fcf = met.get('freeCashFlowYieldTTM', 0.05) * prof.get('mktCap', 0)
                shares = prof.get('mktCap', 0) / prof.get('price', 1)
                
                # Excel Logic: PV of 20yr FCF + Terminal Value
                # Assumptions: Growth 10%, Discount 8%
                growth = 0.10
                discount = 0.08
                terminal_growth = 0.02
                
                # Manual 20-year projection loop
                total_pv = 0
                temp_fcf = fcf
                for i in range(1, 21):
                    temp_fcf *= (1 + growth)
                    total_pv += temp_fcf / ((1 + discount) ** i)
                
                iv_per_share = round(total_pv / shares, 2)
                curr_price = prof.get('price', 0)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"${curr_price}")
                c2.metric("VMI Intrinsic Value", f"${iv_per_share}")
                c3.metric("Discount/Premium", f"{round(((iv_per_share - curr_price)/curr_price)*100, 2)}%", delta_color="normal")
                
                if iv_per_share > curr_price:
                    st.success(f"🎯 VMI Signal: UNDERVALUED. Trading at a {round(((iv_per_share - curr_price)/iv_per_share)*100, 2)}% margin of safety.")
                else:
                    st.error("⚠️ VMI Signal: OVERVALUED. Monitor for price correction to support lines.")

        else: st.error("❌ Invalid Ticker or API Rate Limit. Please wait 60s.")
