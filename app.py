import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 13px; }
    .metric-val { color: #ffffff; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("TERMINAL CONTROLS")
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
sma_toggle = st.sidebar.multiselect("TECHNICAL OVERLAYS", ["SMA 20", "SMA 50", "SMA 200"], default=["SMA 50"])
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR ---
def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    discount_rate = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Staging Terminal for {ticker_sym}...'):
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            # Fetch long history for Support Line identification
            hist = stock.history(period=time_period)
            
            if not hist.empty:
                # --- HEADER & SCORECARDS (Simplified for brevity) ---
                st.header(f"{info.get('longName')} ({ticker_sym})")
                
                # --- TABS ---
                tab_ov, tab_fin, tab_chart, tab_iv = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 20yr IV Model"])

                with tab_ov:
                    st.subheader("Business Summary")
                    st.write(info.get('longBusinessSummary'))

                with tab_fin:
                    st.subheader("Deep Financial Metrics")
                    c_l, c_r = st.columns(2)
                    with c_l:
                        st.markdown(f'<div class="metric-row"><span class="metric-name">P/E Ratio (TTM)</span><span class="metric-val">{info.get("trailingPE", 0):.2f}</span></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-row"><span class="metric-name">Forward P/E</span><span class="metric-val">{info.get("forwardPE", 0):.2f}</span></div>', unsafe_allow_html=True)
                    with c_r:
                        st.markdown(f'<div class="metric-row"><span class="metric-name">ROE (TTM)</span><span class="metric-val">{info.get("returnOnEquity", 0)*100:.2f}%</span></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="metric-row"><span class="metric-name">Shares Outstanding</span><span class="metric-val">{info.get("sharesOutstanding", 0):,.0f}</span></div>', unsafe_allow_html=True)

                with tab_chart:
                    # 1. CALCULATE SMA
                    for sma in sma_toggle:
                        period = int(sma.split(" ")[1])
                        hist[sma] = hist['Close'].rolling(window=period).mean()

                    # 2. IDENTIFY 4 SUPPORT LINES (Pivot Points)
                    # We find the local minima over the selected period
                    lows = hist['Low'].nsmallest(15).values
                    support_levels = []
                    for l in lows:
                        if all(abs(l - s) > (l * 0.02) for s in support_levels): # Group close lines
                            support_levels.append(l)
                        if len(support_levels) == 4: break

                    # 3. CONSTRUCT PLOTLY CHART
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'], name="Price Action")])

                    # Add SMAs
                    colors = {"SMA 20": "cyan", "SMA 50": "orange", "SMA 200": "red"}
                    for sma in sma_toggle:
                        fig.add_trace(go.Scatter(x=hist.index, y=hist[sma], name=sma, line=dict(color=colors[sma], width=1.5)))

                    # Add 4 Support Lines
                    for i, level in enumerate(support_levels):
                        fig.add_hline(y=level, line_dash="dash", line_color="green", 
                                     annotation_text=f"Support {i+1}: ${level:.2f}", 
                                     annotation_position="bottom right")

                    fig.update_layout(template="plotly_dark", height=700, 
                                     xaxis_rangeslider_visible=False,
                                     yaxis_title="Stock Price (USD)",
                                     margin=dict(l=0, r=0, t=20, b=0))
                    
                    st.plotly_chart(fig, use_container_width=True)

                with tab_iv:
                    iv = calculate_vmi_iv(info.get('freeCashflow', 0), info.get('totalDebt', 0), 
                                         info.get('totalCash', 0), info.get('sharesOutstanding', 1), 
                                         info.get('beta', 1.1))
                    st.metric("VMI 20yr IV", f"${iv}")
                    st.metric("Current Market Price", f"${info.get('currentPrice')}")

        except Exception as e:
            st.error(f"Charting Error: {e}")
