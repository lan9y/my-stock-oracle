import streamlit as st
import requests
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
# We use /stable/ for 2026 account compatibility
BASE_URL = "https://financialmodelingprep.com/api/stable"

# --- CUSTOM CSS FOR "STOCKORACLE" LOOK ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; border: 1px solid #4CAF50; padding: 10px; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SIDEBAR CONTROL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2533/2533513.png", width=100)
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("EXECUTE ANALYSIS")

def get_oracle_data(endpoint):
    # Using the ?symbol= format required by 2026 stable endpoints
    url = f"{BASE_URL}/{endpoint}?symbol={ticker}&apikey={API_KEY}"
    try:
        r = requests.get(url)
        res = r.json()
        return res if isinstance(res, list) and len(res) > 0 else None
    except:
        return None

if analyze_btn:
    with st.spinner('Syncing with FactSet-Style Data feeds...'):
        # Global Data Fetch
        profile = get_oracle_data("profile")
        # Fallback for Metrics if stable/key-metrics is restricted
        metrics = get_oracle_data("key-metrics-ttm")
        
        if profile:
            p = profile[0]
            m = metrics[0] if metrics else {}
            
            # --- DASHBOARD TABS ---
            tab_main, tab_fin, tab_val, tab_ai = st.tabs([
                "🏠 Overview", "📊 Financials", "🎯 Intrinsic Value", "🤖 OracleIQ AI"
            ])

            with tab_main:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(p.get('image', ''))
                    st.metric("Price", f"${p.get('price')}", delta=f"{p.get('changes')}%")
                with col2:
                    st.header(p.get('companyName'))
                    st.write(f"**Industry:** {p.get('industry')} | **Exchange:** {p.get('exchangeShortName')}")
                    st.info(p.get('description', 'Data summary unavailable.')[:800] + "...")
                
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                c2.metric("P/E Ratio", round(p.get('price', 0)/p.get('eps', 1), 2) if p.get('eps') else "N/A")
                c3.metric("Volume", f"{p.get('volAvg', 'N/A')}")
                c4.metric("Beta", p.get('beta', 'N/A'))

            with tab_fin:
                st.subheader("Core
