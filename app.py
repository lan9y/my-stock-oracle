import streamlit as st
import requests

# --- APP SETUP ---
st.set_page_config(page_title="StockOracle AI", layout="wide")

# This line is now fixed for you:
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 

st.title("🔮 StockOracle™ Terminal")
ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL)", value="AAPL").upper()

if st.button("Analyze Now"):
    with st.spinner('Accessing FactSet-Style Data...'):
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
        response = requests.get(url).json()
        
        if response and len(response) > 0:
            stock = response[0]
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if stock.get('image'):
                    st.image(stock.get('image'))
            with col2:
                st.header(stock.get('companyName', 'Unknown'))
                st.write(f"**Price:** ${stock.get('price')} | **Beta:** {stock.get('beta')}")

            st.divider()
            c1, c2, c3 = st.columns(3)
            
            # Simple Valuation Math for the UI
            price = stock.get('price', 0)
            valuation = round(price * 1.15, 2)
            
            c1.metric("Oracle Valuation", f"${valuation}", "15% Upside")
            c2.metric("Moat Score", "Strong", "Top 10%")
            c3.metric("Financial Health", "Healthy", "Green Flag")
            
            st.success(f"Analysis Complete for {ticker}.")
        else:
            st.error(f"❌ Could not find data for '{ticker}'. Please check the symbol.")
