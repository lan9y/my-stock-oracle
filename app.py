import streamlit as st
import requests
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="OraclePro™ Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"

# NEWEST 2026 BASE URL FORMAT
BASE_URL = "https://financialmodelingprep.com/stable"

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ Institutional Terminal")

# --- SIDEBAR ---
ticker = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("RUN DEEP SCAN")

def fetch_oracle(path):
    # This is the modern 2026 query format: /stable/path?symbol=TICKER&apikey=KEY
    url = f"{BASE_URL}/{path}?symbol={ticker}&apikey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data if isinstance(data, list) and len(data) > 0 else None
    except:
        return None

if analyze_btn:
    with st.spinner('Accessing 2026 Data Streams...'):
        # 1. Fetch Core Data Blocks
        profile = fetch_oracle("profile")
        ratios = fetch_oracle("ratios-ttm")
        income = fetch_oracle("income-statement") # May be restricted on some free plans

        if profile:
            p = profile[0]
            r = ratios[0] if ratios else {}
            
            # --- NAVIGATION TABS ---
            tab_ov, tab_fin, tab_val, tab_ai = st.tabs([
                "🏠 Overview", "📊 Financials", "🎯 Intrinsic Value", "🤖 OracleIQ AI"
            ])

            with tab_ov:
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.image(p.get('image', ''))
                    st.metric("Price", f"${p.get('price')}", delta=f"{p.get('changes')}%")
                with c2:
                    st.header(p.get('companyName'))
                    st.write(f"**Sector:** {p.get('sector')} | **Industry:** {p.get('industry')}")
                    st.info(p.get('description', 'Description unavailable.')[:1000] + "...")
                
                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Market Cap", f"${round(p.get('mktCap', 0)/1e9, 2)}B")
                m2.metric("P/E Ratio", round(r.get('priceEarningsRatioTTM', 0), 2) if r.get('priceEarningsRatioTTM') else "N/A")
                m3.metric("ROIC", f"{round(r.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%" if r.get('returnOnCapitalEmployedTTM') else "N/A")
                m4.metric("Div. Yield", f"{round(p.get('lastDiv', 0)/p.get('price', 1)*100, 2)}%")

            with tab_fin:
                st.subheader("Historical Income Data")
                if income:
                    df = pd.DataFrame(income)[['date', 'revenue', 'netIncome', 'eps']]
                    st.dataframe(df.set_index('date'), use_container_width=True)
                else:
                    st.warning("⚠️ Full Income Statements are limited on the free 2026 plan. Showing available TTM data.")
                    st.write(f"**Last Reported EPS:** ${p.get('eps', 'N/A')}")

            with tab_val:
                st.subheader("OracleIQ™ Intrinsic Value Model")
                eps = p.get('eps', 0)
                price = p.get('price', 0)
                # Benjamin Graham Growth Formula (Calculated by App)
                fair_value = round(eps * (8.5 + 20), 2) if eps and eps > 0 else round(price * 1.10, 2)
                upside = round(((fair_value - price) / price) * 100, 2)
                
                v1, v2 = st.columns(2)
                v1.metric("Oracle Fair Value", f"${fair_value}")
                v2.metric("Safety Margin", f"{upside}%", delta=f"{upside}%")
                
                if upside > 15:
                    st.success("✅ UNDERVALUED: Current price is below OracleIQ targets.")
                else:
                    st.warning("⚖️ FAIR VALUE: Market price aligns with fundamentals.")

            with tab_ai:
                st.subheader("🤖 OracleIQ™ AI Insights")
                # Automated Moat Analysis
                roic_val = r.get('returnOnCapitalEmployedTTM', 0)
                st.markdown(f"""
                ### 🧠 AI Verdict for {ticker}:
                * **Moat Rating:** {'Wide Moat' if roic_val > 0.15 else 'Narrow Moat'}. The Return on Capital is **{round(roic_val*100, 2)}%**.
                * **Financial Strength:** {'High' if p.get('mktCap', 0) > 50e9 else 'Moderate'}.
                * **AI Commentary:** {p.get('companyName')} displays a {'strong' if roic_val > 0.1 else 'competitive'} position in the {p.get('sector')} sector. {'Recommend watching for dips.' if upside < 5 else 'Current valuation is attractive.'}
                """)
        else:
            st.error("❌ No data found. Try a major US ticker like AAPL or NVDA.")
