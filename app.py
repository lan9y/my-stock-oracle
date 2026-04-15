import streamlit as st
import requests
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- STYLE ---
st.markdown("""
    <style>
    .metric-card { background-color: #0d1117; border: 1px solid #30363d; padding: 15px; border-radius: 10px; text-align: center; }
    .metric-label { color: #8b949e; font-size: 11px; text-transform: uppercase; font-weight: bold; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SAVING CREDITS: CACHING ENGINE ---
@st.cache_data(ttl=900) # Remember data for 15 minutes
def get_oracle_data(endpoint, ticker):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            res = response.json()
            return res[0] if isinstance(res, list) and len(res) > 0 else None
    except:
        return None
    return None

# --- SIDEBAR ---
ticker_input = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE ANALYSIS")

if analyze_btn:
    ticker = ticker_input
    with st.spinner(f'Analyzing {ticker}...'):
        # Fetching only the bare essentials to stay under rate limits
        p = get_oracle_data("profile", ticker)
        r = get_oracle_data("ratios-ttm", ticker)
        m = get_oracle_data("key-metrics-ttm", ticker)

        if p:
            tab1, tab2 = st.tabs(["🏠 Overview", "📊 Core Financials"])

            with tab1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    if p.get('image'): st.image(p.get('image'))
                with col2:
                    st.header(p.get('companyName'))
                    st.write(p.get('description', '')[:500] + "...")

            with tab2:
                st.subheader("Institutional Grade Metrics")
                r1, r2, r3 = st.columns(3)
                
                # Using the data you specifically requested
                with r1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">P/E Ratio (TTM)</div><div class="metric-value">{round(r.get("priceEarningsRatioTTM", 0), 2) if r else "N/A"}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><div class="metric-label">ROE (TTM)</div><div class="metric-value">{round(r.get("returnOnEquityTTM", 0)*100, 2) if r else "N/A"}%</div></div>', unsafe_allow_html=True)
                
                with r2:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">PEG Ratio</div><div class="metric-value">{round(r.get("priceEarningsGrowthRatioTTM", 0), 2) if r else "N/A"}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><div class="metric-label">ROIC (TTM)</div><div class="metric-value">{round(r.get("returnOnCapitalEmployedTTM", 0)*100, 2) if r else "N/A"}%</div></div>', unsafe_allow_html=True)
                
                with r3:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Div Yield (TTM)</div><div class="metric-value">{round(m.get("dividendYieldTTM", 0)*100, 2) if m else "0.00"}%</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><div class="metric-label">FCF Yield</div><div class="metric-value">{round(m.get("freeCashFlowYieldTTM", 0)*100, 2) if m else "N/A"}%</div></div>', unsafe_allow_html=True)
        else:
            st.error("⚠️ Data not found or Rate Limit hit. Wait 60s.")
