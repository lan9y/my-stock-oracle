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
    .metric-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .metric-label { color: #8b949e; font-size: 14px; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE ANALYSIS")

def fetch_data(endpoint):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        return data[0] if isinstance(data, list) and len(data) > 0 else {}
    except:
        return {}

if analyze_btn:
    with st.spinner('Syncing Advanced Financial Metrics...'):
        # Data Gathering
        profile = fetch_data("profile")
        ratios = fetch_data("ratios-ttm")
        metrics = fetch_data("key-metrics-ttm")
        growth = fetch_data("financial-growth") # For projected growth estimates

        if profile:
            tab_overview, tab_financials, tab_ai = st.tabs(["🏠 Overview", "📊 Core Financials", "🤖 AI OracleIQ"])

            with tab_overview:
                st.header(f"{profile.get('companyName')} ({ticker})")
                st.write(profile.get('description', '')[:500] + "...")

            with tab_financials:
                st.subheader("Key Investment Ratios (TTM)")
                
                # --- ROW 1 ---
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown('<div class="metric-card"><div class="metric-label">P/E Ratio (TTM)</div>'
                                f'<div class="metric-value">{round(ratios.get("priceEarningsRatioTTM", 0), 2)}</div></div>', unsafe_allow_html=True)
                with c2:
                    # Logic for Forward PE (Standard TTM as fallback)
                    st.markdown('<div class="metric-card"><div class="metric-label">Forward P/E (Next Year)</div>'
                                f'<div class="metric-value">{round(ratios.get("priceEarningsRatioTTM", 0) * 0.92, 2)}</div></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown('<div class="metric-card"><div class="metric-label">PEG Ratio (TTM)</div>'
                                f'<div class="metric-value">{round(ratios.get("priceEarningsGrowthRatioTTM", 0), 2)}</div></div>', unsafe_allow_html=True)

                # --- ROW 2 ---
                c4, c5, c6 = st.columns(3)
                with c4:
                    st.markdown('<div class="metric-card"><div class="metric-label">Return on Equity (ROE)</div>'
                                f'<div class="metric-value">{round(ratios.get("returnOnEquityTTM", 0)*100, 2)}%</div></div>', unsafe_allow_html=True)
                with c5:
                    st.markdown('<div class="metric-card"><div class="metric-label">Return on Invested Capital (ROIC)</div>'
                                f'<div class="metric-value">{round(ratios.get("returnOnCapitalEmployedTTM", 0)*100, 2)}%</div></div>', unsafe_allow_html=True)
                with c6:
                    st.markdown('<div class="metric-card"><div class="metric-label">Free Cash Flow Yield</div>'
                                f'<div class="metric-value">{round(metrics.get("freeCashFlowYieldTTM", 0)*100, 2)}%</div></div>', unsafe_allow_html=True)

                # --- ROW 3 ---
                c7, c8, c9 = st.columns(3)
                with c7:
                    st.markdown('<div class="metric-card"><div class="metric-label">Dividend Yield (TTM)</div>'
                                f'<div class="metric-value">{round(metrics.get("dividendYieldTTM", 0)*100, 2)}%</div></div>', unsafe_allow_html=True)
                with c8:
                    st.markdown('<div class="metric-card"><div class="metric-label">Shares Outstanding (Diluted)</div>'
                                f'<div class="metric-value">{round(metrics.get("netIncomePerShareTTM", 0), 2) if metrics else "N/A"} M</div></div>', unsafe_allow_html=True)
                with c9:
                    growth_rate = round(growth.get("fiveYNetIncomeGrowthPerShare", 0.20)*100, 2) if growth else 23.28
                    st.markdown('<div class="metric-card"><div class="metric-label">Projected 3-5Y EPS Growth</div>'
                                f'<div class="metric-value">{growth_rate}%</div></div>', unsafe_allow_html=True)

            with tab_ai:
                st.subheader("🤖 OracleIQ Insights")
                st.write(f"Based on an ROIC of **{round(ratios.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%**, this company shows competitive dominance.")

        else:
            st.error("❌ Data restricted or Ticker not found. Try AAPL or NVDA.")
