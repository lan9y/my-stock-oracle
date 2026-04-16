import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 22px; font-weight: 800; }
    .etf-card { background-color: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
    .etf-ticker { font-weight: 800; color: #ffffff; font-size: 14px; }
    .etf-price { font-size: 18px; font-weight: 700; color: #4CAF50; }
    .moat-badge { padding: 4px 12px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border: 1px solid #4CAF50; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; min-height: 100px; }
    .val-title { color: #8b949e; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .val-price { font-size: 24px; font-weight: 800; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- VALUATION ENGINES ---

def calc_vmi_20yr_dcf(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    dr = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 
    total_pv, cf = 0, fcf
    for y in range(1, 21):
        cf *= (1 + (g1 if y <= 5 else g2 if y <= 10 else g3))
        total_pv += cf / ((1 + dr) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

def calc_10yr_dcf(fcf, shares, growth_rate=0.10, discount_rate=0.08):
    total_pv, cf = 0, fcf
    for y in range(1, 11):
        cf *= (1 + growth_rate)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round(total_pv / shares, 2) if shares > 0 else 0

def calc_10yr_eps_discount(eps, growth_rate=0.15, discount_rate=0.04):
    # Based on your 'Discounted Earnings Per Share' template
    total_pv, cur_eps = 0, eps
    for y in range(1, 11):
        cur_eps *= (1 + growth_rate)
        total_pv += cur_eps / ((1 + discount_rate) ** y)
    return round(total_pv, 2)

# --- MARKET PULSE ---
def get_market_pulse():
    indices = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones"}
    pulse = []
    try:
        data = yf.download(list(indices.keys()), period="2d", interval="1d", progress=False)
        for t in indices:
            price = data['Close'][t].iloc[-1]
            change = ((price - data['Close'][t].iloc[-2]) / data['Close'][t].iloc[-2]) * 100
            pulse.append({"ticker": t, "price": price, "change": change})
    except: pass
    return pulse

# --- MAIN UI ---
st.title("🔮 OraclePro™ VMI Terminal")
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period="1y")
        
        col_main, col_pulse = st.columns([3, 1])

        with col_main:
            # Header logic
            curr_p = info.get('currentPrice', 0)
            st.markdown(f'<div class="live-price-header">{info.get("longName")} ({ticker_sym})</div><div style="font-size:42px; font-weight:800; color:#ffffff;">${curr_p:,.2f}</div>', unsafe_allow_html=True)

            tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Chart", "🎯 Valuation", "🤖 AI Thesis"])

            with tabs[0]:
                st.subheader("Oracle Intelligence Scorecards")
                # [Previous Scorecard Logic Remains Here]
                st.write(info.get('longBusinessSummary'))

            with tabs[1]:
                st.subheader("Deep-Dive Financial Indicators")
                # [Previous Financial Metrics Logic Remains Here]

            with tabs[3]: # VALUATION PAGE
                st.subheader("VMI Multi-Model Fair Value Cluster")
                
                # Data Prep
                fcf = info.get('freeCashflow', 0)
                shares = info.get('sharesOutstanding', 1)
                debt = info.get('totalDebt', 0)
                cash = info.get('totalCash', 0)
                beta = info.get('beta', 1.1)
                eps = info.get('trailingEps', 0)
                bv = info.get('bookValue', 0)
                rev_ps = info.get('totalRevenue', 0) / shares
                growth = info.get('revenueGrowth', 0.1)

                # Execute Models
                v_20dcf = calc_vmi_20yr_dcf(fcf, debt, cash, shares, beta)
                v_10dcf = calc_10yr_dcf(fcf, shares, growth_rate=growth)
                v_eps = calc_10yr_eps_discount(eps, growth_rate=growth)
                v_pb = round(bv * 1.75, 2) # Mean PB Template
                v_psg = round(rev_ps * (growth * 100) * 0.2, 2) # PSG Template

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="valuation-box"><div class="val-title">VMI 20-Year DCF</div><div class="val-price">${v_20dcf}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="valuation-box"><div class="val-title">PSG Model</div><div class="val-price">${v_psg}</div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="valuation-box"><div class="val-title">VMI 10-Year DCF</div><div class="val-price">${v_10dcf}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="valuation-box"><div class="val-title">Mean P/B Model</div><div class="val-price">${v_pb}</div></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="valuation-box"><div class="val-title">10-Year EPS Discount</div><div class="val-price">${v_eps}</div></div>', unsafe_allow_html=True)
                    st.info(f"Avg Fair Value: ${round(np.mean([v_20dcf, v_10dcf, v_eps, v_pb, v_psg]), 2)}")

                st.divider()
                st.subheader("Analyst Price Targets")
                st.metric("Consensus Mean", f"${info.get('targetMeanPrice')}")

        with col_pulse:
            # [Previous Market Pulse Logic Remains Here]
            st.write("Market Pulse Active")

    except Exception as e:
        st.error(f"Sync Error: {e}")
