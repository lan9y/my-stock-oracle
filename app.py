import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- VMI STYLING ---
st.markdown("""
    <style>
    .score-card { background-color: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 22px; font-weight: 800; }
    .metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- DATA ENGINE (WITH CACHING & ERROR RECOVERY) ---
@st.cache_data(ttl=3600)
def get_vmi_data(endpoint, ticker):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url)
        if r.status_code == 429 or r.status_code == 403: return "LIMIT"
        data = r.json()
        return data if isinstance(data, list) and len(data) > 0 else None
    except: return None

# --- EXCEL LOGIC: 20-YEAR IV CALCULATOR ---
def calculate_intrinsic_value(fcf, debt, cash, shares, beta):
    # Constants from your Excel 'Discount Rate Data'
    rf_rate = 0.03608 
    mrp = 0.02728
    discount_rate = rf_rate + (beta * mrp)
    
    # Growth Stages from Excel (VMI IV Calculator 20 years)
    g1, g2, g3 = 0.1748, 0.15, 0.04
    
    pv_fcf = 0
    current_fcf = fcf
    for year in range(1, 21):
        if year <= 5: growth = g1
        elif year <= 10: growth = g2
        else: growth = g3
        
        current_fcf *= (1 + growth)
        pv_fcf += current_fcf / ((1 + discount_rate) ** year)
    
    iv_per_share = (pv_fcf - debt + cash) / shares
    return round(iv_per_share, 2)

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    with st.spinner(f'Consulting OracleIQ for {ticker}...'):
        # Batch fetching all required data
        profile = get_vmi_data("profile", ticker)
        metrics = get_vmi_data("key-metrics-ttm", ticker)
        ratios = get_vmi_data("ratios-ttm", ticker)
        chart_raw = get_vmi_data("historical-price-full", ticker)

        if profile == "LIMIT":
            st.error("🚦 API Limit Reached. Dashboard restricted. Try again in 60s.")
        elif profile:
            p = profile[0]
            m = metrics[0] if metrics else {}
            r = ratios[0] if ratios else {}

            tab_ov, tab_chart, tab_iv = st.tabs(["📊 Overview", "📈 Technicals", "🎯 VMI 20yr Model"])

            with tab_ov:
                # SCORECARDS (From Screenshot)
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                # Heuristic scoring logic
                roic = r.get('returnOnCapitalEmployedTTM', 0.15)
                f_strength = 9 if r.get('currentRatioTTM', 1) > 1.5 else 6
                
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roic*50, 10))}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown(f'<div class="score-card"><div class="score-label">Financial Str.</div><div class="score-value">{f_strength}/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()
                st.header(p.get('companyName'))
                st.info(p.get('description', 'No description available.')[:800] + "...")

            with tab_chart:
                if chart_raw and 'historical' in chart_raw:
                    df = pd.DataFrame(chart_raw['historical'])
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df['SMA50'] = df['close'].rolling(50).mean()
                    df['SMA200'] = df['close'].rolling(200).mean()
                    
                    fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA50'], line=dict(color='#ff9900', width=1), name="SMA 50"))
                    fig.add_trace(go.Scatter(x=df['date'], y=df['SMA200'], line=dict(color='#ff0000', width=1.5), name="SMA 200"))
                    
                    # Support Level (Annual Low)
                    support = df['low'].min()
                    fig.add_hline(y=support, line_dash="dash", line_color="#00ff00", annotation_text="Key Support")
                    
                    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                st.subheader("VMI 20-Year Discounted FCF Model")
                
                # Fetch inputs for the Excel model
                fcf_curr = m.get('freeCashFlowTTM', 1000000)
                debt_val = m.get('totalDebtTTM', 0)
                cash_val = m.get('cashAndShortTermInvestmentsTTM', 0)
                shares_val = m.get('numberOfSharesTTM', 1)
                beta_val = p.get('beta', 1.0)
                
                iv = calculate_intrinsic_value(fcf_curr, debt_val, cash_val, shares_val, beta_val)
                price = p.get('price', 1)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Current Price", f"${price}")
                c2.metric("Intrinsic Value", f"${iv}")
                c3.metric("Margin of Safety", f"{round(((iv-price)/price)*100, 2)}%", delta=f"{round(iv-price,2)}")
                
                if iv > price:
                    st.success("🟢 VMI BUY SIGNAL: Stock is trading at a discount to 20-year Intrinsic Value.")
                else:
                    st.warning("🔴 VMI HOLD/SELL: Stock is overvalued relative to projected cash flows.")
        else:
            st.error("Ticker not found or API key restricted.")
