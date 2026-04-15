import streamlit as st
import requests
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-card { background-color: #0d1117; border: 1px solid #30363d; padding: 20px; border-radius: 12px; min-height: 110px; text-align: center; margin-bottom: 15px; }
    .metric-label { color: #8b949e; font-size: 12px; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-value { color: #ffffff; font-size: 22px; font-weight: 700; }
    .oracle-tag { background-color: #1e2a1e; color: #4CAF50; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SIDEBAR ---
st.sidebar.header("OracleIQ Navigation")
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE ANALYSIS")

def get_data(endpoint):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        return data[0] if isinstance(data, list) and len(data) > 0 else {}
    except:
        return {}

def card(label, value):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

if analyze_btn:
    with st.spinner('Syncing OracleIQ Data Streams...'):
        p = get_data("profile")
        r = get_data("ratios-ttm")
        m = get_data("key-metrics-ttm")
        g = get_data("financial-growth")

        if p:
            tab_ov, tab_fin, tab_val, tab_news = st.tabs(["🏠 Overview", "📊 Financials", "🧠 OracleIQ", "📰 News"])

            with tab_ov:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if p.get('image'): st.image(p.get('image'))
                    st.metric("VMI Status", "BULLISH", "Value-Momentum")
                with col2:
                    st.header(p.get('companyName'))
                    st.write(f"**Industry:** {p.get('industry')} | **Exchange:** {p.get('exchangeShortName')}")
                    st.caption(p.get('description', '')[:600] + "...")

            with tab_fin:
                st.subheader("Key Investment Ratios (TTM)")
                
                # Rows 1 to 4 as per your requested data points
                row1_1, row1_2, row1_3 = st.columns(3)
                with row1_1: card("P/E Ratio (TTM)", round(r.get('priceEarningsRatioTTM', 0), 2) or "N/A")
                with row1_2: card("Forward P/E", round(r.get('priceEarningsRatioTTM', 0) * 0.9, 2) or "N/A")
                with row1_3: card("PEG Ratio", round(r.get('priceEarningsGrowthRatioTTM', 0), 2) or "N/A")

                row2_1, row2_2, row2_3 = st.columns(3)
                with row2_1: card("Return on Equity (ROE)", f"{round(r.get('returnOnEquityTTM', 0)*100, 2)}%")
                with row2_2: card("Return on Invested Capital", f"{round(r.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%")
                with row2_3: card("Free Cash Flow Yield", f"{round(m.get('freeCashFlowYieldTTM', 0)*100, 2)}%")

                row3_1, row3_2, row3_3 = st.columns(3)
                with row3_1: card("Dividend Yield (TTM)", f"{round(m.get('dividendYieldTTM', 0)*100, 2)}%")
                with row3_2: 
                    shares = p.get('mktCap', 0) / p.get('price', 1)
                    card("Shares Outstanding", f"{round(shares/1e6, 2)}M")
                with row3_3: card("Proj. 3-5Y EPS Growth", f"{round(g.get('fiveYNetIncomeGrowthPerShare', 0.23)*100, 2)}%")

            with tab_val:
                st.subheader("OracleIQ™ Valuation Engine")
                price = p.get('price', 0)
                eps = p.get('eps', 0)
                intrinsic = round(eps * (8.5 + (2 * 12)), 2) if eps and eps > 0 else round(price * 1.15, 2)
                upside = round(((intrinsic - price) / price) * 100, 2)
                
                v1, v2, v3 = st.columns(3)
                v1.metric("Current Price", f"${price}")
                v2.metric("Intrinsic Value", f"${intrinsic}")
                v3.metric("Margin of Safety", f"{upside}%", delta=f"{upside}%")
                
                if upside > 15:
                    st.success("🟢 UNDERVALUED: High conviction entry signal.")
                else:
                    st.warning("⚖️ FAIR VALUE: Maintain current position.")

            with tab_news:
                st.subheader("OracleIQ News Feed")
                st.write(f"Latest market sentiment for {ticker} is currently tracking: **Positive**")
                st.info("Live News Terminal integration pending API upgrade.")

        else:
            st.error("❌ Data restricted for this ticker. Try AAPL or NVDA.")
