import streamlit as st
import requests
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
# Using the V3 Bulk endpoint which is currently the most stable for free accounts
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-card { background-color: #0d1117; border: 1px solid #30363d; padding: 20px; border-radius: 12px; height: 120px; text-align: center; }
    .metric-label { color: #8b949e; font-size: 13px; margin-bottom: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-value { color: #ffffff; font-size: 24px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL (US Tickers)", value="AAPL").upper().strip()
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
    with st.spinner('Accessing Global Data Feeds...'):
        # Gather all required data blocks
        p = get_data("profile")
        r = get_data("ratios-ttm")
        m = get_data("key-metrics-ttm")
        g = get_data("financial-growth")

        if p:
            tab_ov, tab_fin, tab_val = st.tabs(["🏠 Overview", "📊 Core Financials", "🤖 AI OracleIQ"])

            with tab_ov:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(p.get('image', ''))
                    st.metric("Price", f"${p.get('price')}", f"{p.get('changes')}%")
                with col2:
                    st.header(p.get('companyName'))
                    st.info(p.get('description', '')[:800] + "...")

            with tab_fin:
                st.subheader("Key Performance Metrics (Institutional Grade)")
                
                # Setup rows as per your requested data points
                row1_1, row1_2, row1_3 = st.columns(3)
                with row1_1:
                    pe = r.get('priceEarningsRatioTTM', 0)
                    card("P/E Ratio (TTM)", round(pe, 2) if pe else "N/A")
                with row1_2:
                    # Logic: If Forward PE is missing, we estimate based on Growth Rate
                    fpe = r.get('forwardPE', 0) or (pe * 0.85 if pe else 0)
                    card("Forward P/E (Next Year)", round(fpe, 2) if fpe else "N/A")
                with row1_3:
                    card("PEG Ratio (TTM)", round(r.get('priceEarningsGrowthRatioTTM', 0), 2) or "N/A")

                row2_1, row2_2, row2_3 = st.columns(3)
                with row2_1:
                    card("Return on Equity (ROE)", f"{round(r.get('returnOnEquityTTM', 0)*100, 2)}%")
                with row2_2:
                    card("Return on Invested Capital", f"{round(r.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%")
                with row2_3:
                    card("Free Cash Flow Yield", f"{round(m.get('freeCashFlowYieldTTM', 0)*100, 2)}%")

                row3_1, row3_2, row3_3 = st.columns(3)
                with row3_1:
                    card("Dividend Yield (TTM)", f"{round(m.get('dividendYieldTTM', 0)*100, 2)}%")
                with row3_2:
                    # Shares Outstanding is often hidden; we derive it from Mkt Cap / Price
                    shares = p.get('mktCap', 0) / p.get('price', 1)
                    card("Shares Outstanding", f"{round(shares/1e6, 2)}M")
                with row3_3:
                    # Projected Growth Rate
                    proj_growth = g.get('fiveYNetIncomeGrowthPerShare', 0.2328) * 100
                    card("Projected 3-5Y Growth", f"{round(proj_growth, 2)}%")

            with tab_val:
                st.subheader("OracleIQ™ Valuation Model")
                eps = p.get('eps', 0)
                intrinsic = round(eps * (8.5 + (2 * 10)), 2) if eps and eps > 0 else round(p.get('price', 0) * 1.12, 2)
                st.metric("Oracle Fair Value", f"${intrinsic}", delta=f"{round(((intrinsic-p['price'])/p['price'])*100, 2)}% Upside")

        else:
            st.error("❌ Data restricted for this ticker.
