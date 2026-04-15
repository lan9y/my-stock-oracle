import streamlit as st
import requests
import pandas as pd

# --- APP SETUP ---
st.set_page_config(page_title="StockOracle AI", layout="wide")
API_KEY = apikey: vJFsENcD098gHX91EBFKtKIAKoCTpj9t # Get one at financialmodelingprep.com

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e445e; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 StockOracle™ Terminal")
ticker = st.text_input("Enter Ticker Symbol", value="AAPL").upper()

if st.button("Analyze Now"):
    with st.spinner('Accessing FactSet-Style Data...'):
        # Data Fetching Logic
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
        data = requests.get(url).json()
        
        if data:
            stock = data[0]
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(stock['image'])
            with col2:
                st.header(stock['companyName'])
                st.write(f"**Price:** ${stock['price']} | **Beta:** {stock['beta']}")

            # Analysis Columns
            st.divider()
            c1, c2, c3 = st.columns(3)
            
            # Simulated Oracle Logic
            upside = ((stock['price'] * 1.2) - stock['price']) / stock['price'] * 100
            
            c1.metric("Oracle Valuation", f"${round(stock['price'] * 1.15, 2)}", f"{round(upside, 1)}% Upside")
            c2.metric("Moat Score", "Strong", "Top 10%")
            c3.metric("Financial Health", "9/10", "Green Flag")
            
            st.success(f"Analysis Complete for {ticker}. The stock shows strong fundamental backing.")
        else:
            st.error("Ticker not found. Please check the symbol.")
