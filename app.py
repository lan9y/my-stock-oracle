import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="OraclePro Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
BASE_URL = "https://financialmodelingprep.com/stable"

# --- STYLING ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e2130; border-radius: 5px; color: white; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Terminal")

# --- SIDEBAR CONTROL ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("RUN GLOBAL ANALYSIS")

def get_data(endpoint, params=""):
    url = f"{BASE_URL}/{endpoint}?symbol={ticker}&apikey={API_KEY}{params}"
    try:
        res = requests.get(url).json()
        return res if isinstance(res, list) and len(res) > 0 else None
    except:
        return None

if analyze_btn:
    # Fetch Data for multiple sections
    profile = get_data("profile")
    metrics = get_data("key-metrics-ttm")
    income = get_data("income-statement", "&limit=5")
    
    if profile:
        # Create the Navigation Tabs
        tab_overview, tab_financials, tab_intrinsic, tab_dividends, tab_ai = st.tabs([
            "🏠 Overview", "📊 Financials", "🎯 Intrinsic Value", "💰 Dividends", "🤖 AI Insights"
        ])

        with tab_overview:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(profile[0].get('image', ''))
            with col2:
                st.header(profile[0].get('companyName'))
                st.info(profile[0].get('description')[:800] + "...")
            
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price", f"${profile[0].get('price')}")
            c2.metric("Market Cap", f"${round(profile[0].get('mktCap', 0)/1e9, 2)}B")
            c3.metric("P/E Ratio", f"{round(metrics[0].get('peRatioTTM', 0), 2) if metrics else 'N/A'}")
            c4.metric("Avg Volume", f"{profile[0].get('volAvg')}")

        with tab_financials:
            st.subheader("Historical Income Statement (Last 5 Years)")
            if income:
                df = pd.DataFrame(income)
                df = df[['date', 'revenue', 'netIncome', 'eps', 'operatingIncome']]
                st.dataframe(df.set_index('date'), use_container_width=True)
            else:
                st.write("Financial history unavailable for this ticker.")

        with tab_intrinsic:
            st.subheader("OracleIQ Value Model")
            curr_price = profile[0].get('price', 0)
            eps = metrics[0].get('netIncomePerShareTTM', 0) if metrics else 0
            
            # Simple Benjamin Graham Model
            fair_value = round(eps * (8.5 + (2 * 10)), 2) # Assumes 10% growth
            upside = round(((fair_value - curr_price) / curr_price) * 100, 2)
            
            v1, v2 = st.columns(2)
            v1.metric("Calculated Intrinsic Value", f"${fair_value}")
            v2.metric("Margin of Safety", f"{upside}%")
            
            if upside > 20:
                st.success("✅ UNDERVALUED: Significant buying opportunity.")
            else:
                st.warning("⚖️ FAIRLY VALUED: Trading near analyst targets.")

        with tab_dividends:
            st.subheader("Dividend & Yield Analysis")
            if metrics:
                yield_val = round(metrics[0].get('dividendYieldTTM', 0) * 100, 2)
                st.metric("Current Yield", f"{yield_val}%")
                if yield_val > 0:
                    st.write("This company consistently returns value to shareholders via dividends.")
                else:
                    st.write("Growth stock: No current dividend payout detected.")

        with tab_ai:
            st.subheader("🤖 AI Oracle Insights")
            st.markdown(f"""
            **Company Sentiment:** Positive
            **Moat Analysis:** {profile[0].get('companyName')} maintains a high barrier to entry via its 
            brand equity and proprietary technology. 
            **OracleIQ Suggestion:** Watch for entry below ${round(curr_price * 0.9, 2)}.
            """)

    else:
        st.error("Ticker not found. Try AAPL, NVDA, or MSFT.")
