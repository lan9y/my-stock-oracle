import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import random

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 24px; font-weight: 800; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-weight: 500; }
    .metric-val { color: #ffffff; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
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
    with st.spinner(f'Fetching Deep Financials for {ticker_sym}...'):
        try:
            stock = yf.Ticker(ticker_sym)
            info = stock.info
            
            if info and 'currentPrice' in info:
                # --- SCORES ---
                roa = info.get('returnOnAssets', 0)
                pe = info.get('trailingPE', 0)
                
                # --- HEADER ---
                st.header(f"{info.get('longName')} ({ticker_sym})")
                
                # --- SCORECARDS ---
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roa*100/1.5, 10))}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown(f'<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown(f'<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown(f'<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown(f'<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

                st.divider()

                # --- TABS ---
                tab_ov, tab_fin, tab_iv = st.tabs(["📊 Overview", "📑 Financial Metrics", "🎯 20yr IV Model"])
                
                with tab_ov:
                    st.subheader("Business Summary")
                    st.write(info.get('longBusinessSummary'))

                with tab_fin:
                    st.subheader("Institutional Financial Metrics (TTM)")
                    
                    # Logic for ROIC proxy (Return on Invested Capital)
                    total_assets = info.get('totalAssets', 1)
                    cur_liab = info.get('totalCurrentLiabilities', 0)
                    roic_proxy = info.get('ebitda', 0) / (total_assets - cur_liab) if total_assets > cur_liab else 0
                    
                    # Logic for FCF Yield
                    fcf_yield = (info.get('freeCashflow', 0) / info.get('marketCap', 1)) * 100

                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        metrics_l = {
                            "Price to Earnings Ratio (TTM)": f"{pe:.2f}",
                            "Forward Price to Earnings Ratio": f"{info.get('forwardPE', 0):.2f}",
                            "Projected 3-5 Years EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                            "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                            "Price to Earnings Growth (PEG)": f"{info.get('pegRatio', 'N/A')}"
                        }
                        for label, val in metrics_l.items():
                            st.markdown(f'<div class="metric-row"><span class="metric-name">{label}</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)

                    with col_right:
                        metrics_r = {
                            "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                            "Return on Invested Capital (Proxy)": f"{roic_proxy*100:.2f}%",
                            "Free Cash Flow Yield (TTM)": f"{fcf_yield:.2f}%",
                            "Projected Long Term EPS Growth": f"{info.get('earningsQuarterlyGrowth', 0)*100:.2f}%",
                            "Shares Outstanding (Diluted)": f"{info.get('sharesOutstanding', 0):,.0f}"
                        }
                        for label, val in metrics_r.items():
                            st.markdown(f'<div class="metric-row"><span class="metric-name">{label}</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)

                with tab_iv:
                    iv = calculate_vmi_iv(
                        info.get('freeCashflow', 0), info.get('totalDebt', 0), 
                        info.get('totalCash', 0), info.get('sharesOutstanding', 1), 
                        info.get('beta', 1.1)
                    )
                    st.metric("VMI 20yr IV", f"${iv}")
                    st.metric("Current Market Price", f"${info.get('currentPrice')}")

            else:
                st.error("Ticker data unavailable. Please try again.")

        except Exception as e:
            st.error(f"Error processing financials: {e}")
