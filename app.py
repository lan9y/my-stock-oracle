import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ Open Terminal", layout="wide")

st.title("🔮 OraclePro™ Open-Source Terminal")
st.markdown("🚀 *Powered by Yahoo Finance (No API Key Required)*")

# --- SIDEBAR ---
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR (EXCEL LOGIC) ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    # Your Excel Constants
    rf, mrp = 0.03608, 0.02728 
    discount_rate = rf + (beta * mrp)
    # Your 3-Stage Growth Rates
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Extracting Global Market Data for {ticker_sym}...'):
        try:
            # Fetch Stock Data
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            hist = stock.history(period="1y")
            
            # --- DASHBOARD LAYOUT ---
            tab_ov, tab_chart, tab_iv = st.tabs(["📊 Overview", "📈 Chart", "🎯 20yr IV Model"])

            with tab_ov:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.header(f"{info.get('longName', ticker_sym)}")
                    st.write(f"**Sector:** {info.get('sector')} | **Industry:** {info.get('industry')}")
                with col2:
                    roic = info.get('returnOnAssets', 0) * 2 # ROA as proxy for ROIC
                    moat = "WIDE MOAT" if roic > 0.15 else "NARROW MOAT"
                    st.success(f"🛡️ {moat}")

                st.divider()
                st.subheader("Business Description")
                st.write(info.get('longBusinessSummary', "No description available."))

            with tab_chart:
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index, open=hist['Open'], high=hist['High'], 
                    low=hist['Low'], close=hist['Close'], name="Price")])
                fig.update_layout(template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)

            with tab_iv:
                # Scavenge metrics for the VMI formula
                fcf = info.get('freeCashflow', 0)
                debt = info.get('totalDebt', 0)
                cash = info.get('totalCash', 0)
                shares = info.get('sharesOutstanding', 1)
                beta = info.get('beta', 1.1)

                iv_price = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                market_p = info.get('currentPrice', 1)

                c1, c2, c3 = st.columns(3)
                c1.metric("VMI 20yr IV", f"${iv_price}")
                c2.metric("Market Price", f"${market_p}")
                if market_p > 0:
                    mos = round(((iv_price - market_p) / market_p) * 100, 2)
                    c3.metric("Margin of Safety", f"{mos}%")

        except Exception as e:
            st.error(f"Error: {e}. Please ensure the ticker symbol is correct.")
