import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
import random

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 14px; font-weight: 500; }
    .metric-val { color: #ffffff; font-weight: 700; font-size: 14px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("TERMINAL CONTROLS")
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
sma_toggle = st.sidebar.multiselect("TECHNICAL OVERLAYS", ["SMA 20", "SMA 50", "SMA 200"], default=["SMA 50", "SMA 200"])
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

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
    with st.spinner('Syncing Institutional Data...'):
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            hist = stock.history(period=time_period)
            
            if info and 'currentPrice' in info:
                # --- CALC SCORES FOR OVERVIEW ---
                roa = info.get('returnOnAssets', 0)
                pe = info.get('trailingPE', 0)
                fwd_pe = info.get('forwardPE', 1)
                rev_growth = info.get('revenueGrowth', 0)
                
                # Dynamic Score Logic
                profit_score = int(min(roa * 100 / 1.5, 10)) if roa else 5
                moat_score = 9 if roa > 0.12 else 7
                val_score = 10 - int(min(fwd_pe / 8, 9)) if fwd_pe > 0 else 5
                
                # --- HEADER ---
                st.header(f"{info.get('longName')} ({ticker_sym})")
                
                # --- TABS ---
                tab_ov, tab_fin, tab_chart, tab_iv = st.tabs(["📊 Overview", "📑 Financial Metrics", "📈 Advanced Chart", "🎯 20yr IV Model"])

                with tab_ov:
                    st.subheader("Oracle Intelligence Scorecards")
                    s1, s2, s3, s4, s5, s6 = st.columns(6)
                    with s1: st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                    with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{profit_score}/10</div></div>', unsafe_allow_html=True)
                    with s3: st.markdown(f'<div class="score-card"><div class="score-label">Growth</div><div class="score-value">{int(min(rev_growth*100, 10))}/10</div></div>', unsafe_allow_html=True)
                    with s4: st.markdown(f'<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">{moat_score}/10</div></div>', unsafe_allow_html=True)
                    with s5: st.markdown(f'<div class="score-card"><div class="score-label">Financial Strength</div><div class="score-value">{int(min(info.get("currentRatio",0)*4, 10))}/10</div></div>', unsafe_allow_html=True)
                    with s6: st.markdown(f'<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">{val_score}/10</div></div>', unsafe_allow_html=True)
                    
                    st.divider()
                    st.subheader("Business Segment Analysis")
                    st.write(info.get('longBusinessSummary'))

                with tab_fin:
                    st.subheader("Deep-Dive Financial Indicators (TTM)")
                    col_l, col_r = st.columns(2)
                    
                    # Logic for custom metrics
                    roic = info.get('returnOnAssets', 0) * 1.8 # ROIC Proxy
                    fcf_yield = (info.get('freeCashflow', 0) / info.get('marketCap', 1)) * 100
                    
                    with col_l:
                        l_metrics = {
                            "Price to Earnings Ratio (TTM)": f"{pe:.2f}",
                            "Forward Price to Earnings Ratio (Next Year)": f"{info.get('forwardPE', 0):.2f}",
                            "Projected 3-5 Years EPS Growth Rate": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                            "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                            "Price to Earnings Growth Ratio (TTM)": f"{info.get('pegRatio', 'N/A')}"
                        }
                        for k, v in l_metrics.items():
                            st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

                    with col_r:
                        r_metrics = {
                            "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                            "Return on Invested Capital (TTM)": f"{roic*100:.2f}%",
                            "Free Cash Flow Yield (TTM)": f"{fcf_yield:.2f}%",
                            "Projected Long Term EPS Growth Rate": f"{info.get('earningsQuarterlyGrowth', 0)*100:.2f}%",
                            "Shares Outstanding (Diluted Average)": f"{info.get('sharesOutstanding', 0):,.0f}"
                        }
                        for k, v in r_metrics.items():
                            st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

                with tab_chart:
                    # SMA Calculation
                    for sma in sma_toggle:
                        p = int(sma.split(" ")[1])
                        hist[sma] = hist['Close'].rolling(window=p).mean()

                    # Support Detection (Lowest 4 Points)
                    support_lvls = sorted(list(set(hist['Low'].nsmallest(10).round(2))))[:4]

                    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price")])
                    
                    # Add SMA Lines
                    colors = {"SMA 20": "cyan", "SMA 50": "orange", "SMA 200": "red"}
                    for sma in sma_toggle:
                        fig.add_trace(go.Scatter(x=hist.index, y=hist[sma], name=sma, line=dict(color=colors[sma], width=1.2)))
                    
                    # Add Support Lines
                    for i, lvl in enumerate(support_lvls):
                        fig.add_hline(y=lvl, line_dash="dash", line_color="green", opacity=0.6, annotation_text=f"S{i+1}: ${lvl}")

                    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)

                with tab_iv:
                    iv = calculate_vmi_iv(info.get('freeCashflow', 0), info.get('totalDebt', 0), 
                                         info.get('totalCash', 0), info.get('sharesOutstanding', 1), 
                                         info.get('beta', 1.1))
                    mkt_p = info.get('currentPrice', 1)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("VMI 20yr IV", f"${iv}")
                    c2.metric("Market Price", f"${mkt_p}")
                    if mkt_p > 0:
                        mos = round(((iv - mkt_p) / mkt_p) * 100, 2)
                        st.metric("Margin of Safety", f"{mos}%")

        except Exception as e:
            st.error(f"Terminal Sync Error: {e}")
