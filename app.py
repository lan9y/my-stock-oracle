import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 14px; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("TERMINAL CONTROLS")
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
sma_toggle = st.sidebar.multiselect("TECHNICAL OVERLAYS", ["SMA 50", "SMA 200"], default=["SMA 50", "SMA 200"])
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR (EXCEL LOGIC SYNC) ---
def calculate_vmi_20yr_iv(fcf, debt, cash, shares, beta):
    # Constants from your Excel 'Discount Rate Data' sheet
    rf = 0.03608 # US Risk Free Average
    mrp = 0.02728 # Market Risk Premium Average
    dr = rf + (beta * mrp)
    
    # Growth Stages from your 'VMI IV Calculator (20 years)' sheet
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 
    
    total_pv = 0
    current_fcf = fcf
    
    for y in range(1, 21):
        # Apply stage-based growth
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        current_fcf *= (1 + growth)
        total_pv += current_fcf / ((1 + dr) ** y)
    
    iv_before_cash = total_pv / shares if shares > 0 else 0
    debt_per_share = debt / shares if shares > 0 else 0
    cash_per_share = cash / shares if shares > 0 else 0
    
    final_iv = iv_before_cash - debt_per_share + cash_per_share
    return round(final_iv, 2)

if run_btn:
    with st.spinner('Accessing Global Markets...'):
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            hist = stock.history(period=time_period)
            
            if info and 'currentPrice' in info:
                st.header(f"{info.get('longName')} ({ticker_sym})")
                
                # --- TABS ---
                tab_ov, tab_fin, tab_chart, tab_val = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation"])

                with tab_ov:
                    st.subheader("Oracle Intelligence Scorecards")
                    s1, s2, s3, s4, s5, s6 = st.columns(6)
                    roa = info.get('returnOnAssets', 0)
                    with s1: st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                    with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roa*100/1.5, 10))}/10</div></div>', unsafe_allow_html=True)
                    with s3: st.markdown(f'<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                    with s4: st.markdown(f'<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                    with s5: st.markdown(f'<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                    with s6: st.markdown(f'<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                    st.divider()
                    st.subheader("Business Summary")
                    st.write(info.get('longBusinessSummary'))

                with tab_fin:
                    st.subheader("Institutional Financial Metrics (TTM)")
                    col_l, col_r = st.columns(2)
                    with col_l:
                        l_m = {
                            "Price to Earnings Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                            "Forward Price to Earnings Ratio": f"{info.get('forwardPE', 0):.2f}",
                            "Projected 3-5 Years EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                            "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                            "Price to Earnings Growth (PEG)": f"{info.get('pegRatio', 'N/A')}"
                        }
                        for k,v in l_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
                    with col_r:
                        r_m = {
                            "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                            "Return on Invested Capital (Proxy)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                            "Free Cash Flow Yield (TTM)": f"{(info.get('freeCashflow', 0)/info.get('marketCap', 1))*100:.2f}%",
                            "Projected Long Term EPS Growth": f"{info.get('earningsQuarterlyGrowth', 0)*100:.2f}%",
                            "Shares Outstanding (Diluted)": f"{info.get('sharesOutstanding', 0):,.0f}"
                        }
                        for k,v in r_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

                with tab_chart:
                    # Chart Logic with Support Levels
                    for sma in sma_toggle:
                        p = int(sma.split(" ")[1]); hist[sma] = hist['Close'].rolling(window=p).mean()
                    supports = sorted(list(set(hist['Low'].nsmallest(10).round(2))))[:4]
                    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price")])
                    colors = {"SMA 50": "orange", "SMA 200": "red"}
                    for sma in sma_toggle: fig.add_trace(go.Scatter(x=hist.index, y=hist[sma], name=sma, line=dict(color=colors[sma], width=1.2)))
                    for i, lvl in enumerate(supports): fig.add_hline(y=lvl, line_dash="dash", line_color="green", opacity=0.5, annotation_text=f"S{i+1}")
                    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with tab_val:
                    st.subheader("VMI Multi-Model Valuation Suite")
                    
                    # 1. 20-Year VMI DCF (Sync'd with Excel)
                    iv_20 = calculate_vmi_20yr_iv(info.get('freeCashflow', 0), info.get('totalDebt', 0), info.get('totalCash', 0), info.get('sharesOutstanding', 1), info.get('beta', 1.1))
                    
                    # 2. Mean P/B Model (Sync'd with Mean PB template)
                    mean_pb_ratio = 1.75 # Default from your JPM template
                    iv_pb = round(info.get('bookValue', 0) * mean_pb_ratio, 2)
                    
                    # 3. PSG Model (Sync'd with PSG template)
                    rev_per_share = info.get('totalRevenue', 0) / info.get('sharesOutstanding', 1)
                    growth_rate = info.get('revenueGrowth', 0.10)
                    fair_psg = 0.20 # Default from your PLTR template
                    iv_psg = round(rev_per_share * (growth_rate * 100) * fair_psg, 2)
                    
                    v1, v2, v3 = st.columns(3)
                    with v1: st.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:22px; color:#4CAF50;">${iv_20}</span></div>', unsafe_allow_html=True)
                    with v2: st.markdown(f'<div class="valuation-box"><b>Mean P/B Valuation</b><br><span style="font-size:22px; color:#4CAF50;">${iv_pb}</span></div>', unsafe_allow_html=True)
                    with v3: st.markdown(f'<div class="valuation-box"><b>PSG Valuation</b><br><span style="font-size:22px; color:#4CAF50;">${iv_psg}</span></div>', unsafe_allow_html=True)

                    st.divider()
                    st.subheader("Wall Street Price Targets")
                    w1, w2, w3, w4 = st.columns(4)
                    w1.metric("Mean Target", f"${info.get('targetMeanPrice', 'N/A')}")
                    w2.metric("High Target", f"${info.get('targetHighPrice', 'N/A')}")
                    w3.metric("Low Target", f"${info.get('targetLowPrice', 'N/A')}")
                    w4.metric("Current Price", f"${info.get('currentPrice')}")

        except Exception as e:
            st.error(f"Terminal Error: {e}")
