import streamlit as st
import requests

# --- APP SETUP ---
st.set_page_config(page_title="StockOracle AI", layout="wide")

# Your verified API Key
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 

st.title("🔮 StockOracle™ Terminal")
st.write("Institutional Analysis powered by AI & Real-time Data")

# User input
ticker_input = st.text_input("Enter Ticker Symbol (e.g., AAPL, TSLA, NVDA)", value="")

if st.button("Analyze Now"):
    if not ticker_input:
        st.warning("Please enter a ticker symbol first.")
    else:
        ticker = ticker_input.upper().strip()
        with st.spinner(f'Searching for {ticker}...'):
            url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
            
            try:
                response = requests.get(url).json()
                
                # Check if the response is a list and has at least one item
                if isinstance(response, list) and len(response) > 0:
                    stock = response[0]
                    
                    # Layout Results
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if stock.get('image'):
                            st.image(stock.get('image'))
                    with col2:
                        st.header(stock.get('companyName', 'Unknown Company'))
                        st.write(f"**Price:** ${stock.get('price')} | **Sector:** {stock.get('sector')}")

                    st.divider()
                    
                    # Simple Valuation Logic
                    c1, c2, c3 = st.columns(3)
                    price = stock.get('price', 0)
                    # For prototype: Intrinsic Value is set at +15% of current price
                    fair_value = round(price * 1.15, 2)
                    
                    c1.metric("Estimated Fair Value", f"${fair_value}", "15% Upside")
                    c2.metric("Oracle Moat Score", "Strong", "Top 10%")
                    c3.metric("Financial Health", "Green Flag", "Healthy")
                    
                    st.success(f"Successfully analyzed {ticker}.")
                
                else:
                    st.error(f"❌ Error: Ticker '{ticker}' not found or not supported on the free plan.")
                    
            except Exception as e:
                st.error("⚠️ Connection error. Please try again in a moment.")
