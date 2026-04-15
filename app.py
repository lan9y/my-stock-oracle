import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="OracleIQ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
# Using the stable endpoint which is required for 2026 accounts
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OracleIQ™ Professional Terminal")

# --- SIDEBAR ---
st.sidebar.header("Control Center")
ticker = st.sidebar.text_input("Enter Ticker", value="AAPL").upper().strip()
run_btn = st.sidebar.button("Execute Deep Scan")

def fetch(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}/{ticker}?apikey={API_KEY}{params}"
    try:
        r = requests.get(url)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return data
        return None
    except:
        return None

if run_btn:
    # Pre-fetch data for all modules
    profile = fetch("profile")
    metrics = fetch("key-metrics-ttm")
    income = fetch("income-statement", "&limit=5")
    ratios = fetch("ratios-ttm")

    if profile:
        p = profile[0]
        m = metrics[0] if metrics else {}
        r = ratios[0] if ratios else {}

        # NAVIGATION TABS
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview", "🧾 Financials", "⚖️ Intrinsic Value", "💎 Dividend/Metrics", "🧠 AI OracleIQ"
        ])

        with tab1:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(p.get('image', ''))
                st.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
            with col2:
                st.header(p.get('companyName'))
                st.subheader(f"Current Price: ${p.get('price')}")
                st.write(p.get('description', 'No description available.')[:1200] + "...")

        with tab2:
            st.subheader("Historical Performance (5-Year View)")
            if income:
                df = pd.DataFrame(income)[['date', 'revenue', 'netIncome', 'eps', 'operatingIncome']]
                st.table(df)
            else:
                st.warning("Historical financials restricted on free tier.")

        with tab3:
            st.subheader("OracleIQ™ Intrinsic Value Engine")
            # Logic: Using TTM EPS and assumed growth
            eps = m.get('netIncomePerShareTTM', 0)
            if eps > 0:
                # Benjamin Graham Revised Formula
                fair_value = round(eps * (8.5 + 2*10), 2) 
                upside = round(((fair_value - p['price']) / p['price']) * 100, 2)
                
                v1, v2 = st.columns(2)
                v1.metric("Calculated Fair Value", f"${fair_value}")
                v2.metric("Margin of Safety", f"{upside}%", delta=f"{upside}%")
                
                if upside > 20:
                    st.success("🎯 ACTION: High Margin of Safety detected.")
                else:
                    st.info("⚖️ ACTION: Trading near historical valuation.")
            else:
                st.error("Intrinsic Value cannot be calculated for loss-making companies.")

        with tab4:
            st.subheader("Profitability & Dividends")
            c1, c2, c3 = st.columns(3)
            c1.metric("Dividend Yield", f"{round(m.get('dividendYieldTTM', 0)*100, 2)}%")
            c2.metric("ROE", f"{round(r.get('returnOnEquityTTM', 0)*100, 2)}%")
            c3.metric("P/E Ratio", round(r.get('priceEarningsRatioTTM', 0), 2))

        with tab5:
            st.subheader("🤖 AI OracleIQ Insights")
            roic = r.get('returnOnCapitalEmployedTTM', 0)
            
            st.write(f"**Moat Analysis:** {'✅ Wide Moat' if roic > 0.15 else '⚠️ Narrow Moat'}")
            st.write(f"**Verdict:** {p['companyName']} shows a {'Strong' if roic > 0.15 else 'Neutral'} competitive advantage based on its capital returns of {round(roic*100, 2)}%.")
            st.progress(min(int(roic * 100), 100) if roic > 0 else 0)

    else:
        st.error("❌ Data not found. Ensure you are using a US Ticker (e.g., AAPL, MSFT, TSLA) and have not hit your 250-call daily limit.")
