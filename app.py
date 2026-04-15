import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="OraclePro Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
BASE_URL = "https://financialmodelingprep.com/api/v3" # Using V3 for better compatibility with free metrics

st.title("🔮 OraclePro™ Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("RUN GLOBAL ANALYSIS")

def get_json(url):
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

if analyze_btn:
    with st.spinner(f'Synchronizing Oracle Data for {ticker}...'):
        # 1. Fetch Company Profile
        profile_data = get_json(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}")
        # 2. Fetch Key Metrics (For Market Cap & Dividends)
        metrics_data = get_json(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}")
        # 3. Fetch Income Statement (For EPS & Financials)
        income_data = get_json(f"{BASE_URL}/income-statement/{ticker}?limit=5&apikey={API_KEY}")
        # 4. Fetch Ratios (For P/E and ROIC)
        ratios_data = get_json(f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}")

        if profile_data:
            p = profile_data[0]
            m = metrics_data[0] if metrics_data else {}
            r = ratios_data[0] if ratios_data else {}
            
            # --- CREATE TABS ---
            tab_overview, tab_financials, tab_intrinsic, tab_dividends, tab_ai = st.tabs([
                "🏠 Overview", "📊 Financials", "🎯 OracleIQ Value", "💰 Dividends", "🤖 AI Insights"
            ])

            with tab_overview:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(p.get('image', ''))
                with col2:
                    st.header(p.get('companyName', ticker))
                    st.write(f"**Sector:** {p.get('sector')} | **Industry:** {p.get('industry')}")
                    st.info(p.get('description', 'No description available.')[:1000] + "...")
                
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                
                # Fetching Market Cap (With fallback calculation)
                price = p.get('price', 0)
                mkt_cap = p.get('mktCap') if p.get('mktCap') else (m.get('marketCapTTM') if m.get('marketCapTTM') else 0)
                
                c1.metric("Current Price", f"${price}")
                c2.metric("Market Cap", f"${round(mkt_cap/1e9, 2)}B" if mkt_cap else "N/A")
                c3.metric("P/E Ratio", round(r.get('priceEarningsRatioTTM', 0), 2) if r.get('priceEarningsRatioTTM') else "N/A")
                c4.metric("ROIC", f"{round(r.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%" if r.get('returnOnCapitalEmployedTTM') else "N/A")

            with tab_financials:
                st.subheader("Last 5 Years Performance")
                if income_data:
                    df = pd.DataFrame(income_data)[['date', 'revenue', 'netIncome', 'eps', 'operatingIncome']]
                    st.dataframe(df.set_index('date'), use_container_width=True)
                else:
                    st.warning("Income statement data restricted on free plan.")

            with tab_intrinsic:
                st.subheader("OracleIQ™ Intrinsic Value Model")
                # Benjamin Graham Formula Logic
                eps = income_data[0].get('eps', 0) if income_data else 0
                if eps > 0:
                    # Intrinsic Value = EPS * (8.5 + 2g) -- assuming 10% growth
                    intrinsic_val = round(eps * (8.5 + 20), 2)
                    upside = round(((intrinsic_val - price) / price) * 100, 2)
                    
                    v1, v2 = st.columns(2)
                    v1.metric("Calculated Fair Value", f"${intrinsic_val}")
                    v2.metric("Upside / Downside", f"{upside}%", delta=f"{upside}%", delta_color="normal")
                    
                    if upside > 15:
                        st.success("🟢 UNDERVALUED: Stock is trading below Oracle Fair Value.")
                    elif upside < -15:
                        st.error("🔴 OVERVALUED: Stock is trading above Oracle Fair Value.")
                    else:
                        st.warning("🟡 FAIR VALUE: Stock is priced accurately by the market.")
                else:
                    st.error("Cannot calculate Intrinsic Value: Company has negative or missing Earnings (EPS).")

            with tab_dividends:
                st.subheader("Dividend Analysis")
                div_yield = m.get('dividendYieldTTM', 0) * 100
                st.metric("Dividend Yield", f"{round(div_yield, 2)}%")
                st.write("**Dividend Consistency:** " + ("High" if div_yield > 2 else "Growth Focused / Low"))

            with tab_ai:
                st.subheader("🤖 OracleIQ AI Sentiment")
                # Automated AI Insights based on fetched data
                roic = r.get('returnOnCapitalEmployedTTM', 0)
                debt_to_equity = r.get('debtEquityRatioTTM', 0)
                
                moat_status = "Wide Moat" if roic > 0.15 else "Narrow/No Moat"
                health_status = "Excellent" if debt_to_equity < 1 else "High Debt Warning"
                
                st.markdown(f"""
                ### 🧠 Oracle Insights for {ticker}:
                * **Moat Rating:** {moat_status}. The company returns **{round(roic*100, 2)}%** on its capital.
                * **Financial Health:** {health_status}. Debt-to-Equity is at **{round(debt_to_equity, 2)}**.
                * **AI Verdict:** Based on current metrics, this company is a **{'Strong Asset' if roic > 0.1 and debt_to_equity < 1.5 else 'Speculative Play'}**.
                """)
        else:
            st.error("❌ Invalid Ticker or API Limit Reached. Try again in 60 seconds.")
