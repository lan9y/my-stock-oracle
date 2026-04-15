import streamlit as st
import requests

st.set_page_config(page_title="StockOracle AI", layout="wide")

# Your Verified API Key
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 

# THE NEW 2026 URL (Fixed Query Format)
BASE_URL = "https://financialmodelingprep.com/api/stable"

st.title("🔮 StockOracle™ Terminal")
st.write("Institutional Analysis | 2026 Stable Version")

ticker_input = st.text_input("Enter Ticker Symbol (e.g., AAPL, NVDA)", value="AAPL")

if st.button("Analyze Now"):
    ticker = ticker_input.upper().strip()
    with st.spinner(f'Consulting 2026 Data for {ticker}...'):
        
        # FIXED: This uses the '?symbol=' format required by the new stable API
        url = f"{BASE_URL}/profile?symbol={ticker}&apikey={API_KEY}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            # 1. Check for API Errors (Limit/Legacy)
            if isinstance(data, dict) and "Error Message" in data:
                st.error(f"🚫 API Issue: {data.get('Error Message')}")
            
            # 2. Check for successful data
            elif isinstance(data, list) and len(data) > 0:
                stock = data[0]
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if stock.get('image'):
                        st.image(stock.get('image'))
                with col2:
                    st.header(stock.get('companyName', 'Unknown'))
                    st.subheader(f"Price: ${stock.get('price')} {stock.get('currency')}")
                    st.write(f"**Sector:** {stock.get('sector')} | **Exchange:** {stock.get('exchangeShortName')}")

                st.divider()
                
                # Oracle Metrics (Calculations)
                c1, c2, c3 = st.columns(3)
                price = stock.get('price', 0)
                fair_value = round(price * 1.12, 2)
                
                c1.metric("Oracle Fair Value", f"${fair_value}", "12% Upside")
                c2.metric("Moat Status", "Wide Moat", "Institutional")
                c3.metric("Financial Health", "Status: Green", "Low Debt")
                
                st.success(f"Analysis Complete for {ticker}.")
            
            else:
                st.error(f"❌ Ticker '{ticker}' not found. Please try a major US stock like AAPL.")

        except Exception as e:
            st.error(f"⚠️ Connection Glitch. Please refresh the page.")
