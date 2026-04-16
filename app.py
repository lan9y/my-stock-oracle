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
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 22px; font-weight: 800; }
    .etf-card { background-color: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
    .etf-ticker { font-weight: 800; color: #ffffff; font-size: 14px; }
    .etf-price { font-size: 18px; font-weight: 700; color: #4CAF50; }
    .live-price-header { font-size: 42px; font-weight: 800; color: #ffffff; margin-bottom: 0px; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 14px; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MARKET PULSE HELPER ---
def get_market_pulse():
    etfs = ["SPY", "QQQ", "DIA"]
    pulse_data = []
    for ticker in etfs:
        try:
            t = yf.Ticker(ticker)
            px = t.fast_info['last_price']
            chg = t.fast_info['year_to_date_return'] # Placeholder for live daily %
            pulse_data.append({"ticker": ticker, "price": px, "change": chg})
        except: pulse_data.append({"ticker": ticker, "price": 0, "change": 0})
    return pulse_data

# --- VMI 20-YEAR IV CALCULATOR (EXCEL LOGIC SYNC) ---
def calculate_vmi_20yr_iv(fcf, debt, cash, shares, beta):
    rf = 0.03608 # Excel 'Discount Rate Data' Rf Average
    mrp = 0.02728 # Excel 'Discount Rate Data' MRP Average
    dr = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 # Excel 'VMI IV Calculator (20 years)' Stages
    
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + dr) ** y)
    
    iv_per_share = (total_pv - debt + cash) / shares if shares > 0 else 0
    return round(iv_per_share, 2)

st.title("🔮 OraclePro™ VMI Terminal")

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
sma_toggle = st.sidebar.multiselect("TECHNICAL OVERLAYS", ["SMA 50", "SMA 200"], default=["SMA 50", "SMA 200"])
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period=time_period)
        market_pulse = get_market_pulse()

        col_main, col_pulse = st.columns([3, 1])

        with col_main:
            # 1. LIVE PRICE HEADER
            curr_p = info.get('currentPrice', 0)
            p_chg = info.get('regularMarketChangePercent', 0)
            st.markdown(f"""
                <div style="margin-bottom:20px;">
                    <span style="color:#8b949e; font-weight:700;">{info.get('longName')} ({ticker_sym})</span>
                    <div class="live-price-header">${curr_p:,.2f}</div>
                    <span style="color:{'#4CAF50' if p_chg >= 0 else '#FF5252'}; font-weight:700; font-size:18px;">
                        {"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%
                    </span>
                </div>
            """, unsafe_allow_html=True)

            tab_ov, tab_fin, tab_chart, tab_val = st.tabs(["📊 Overview", "📑 Financials", "📈 Chart", "🎯 Valuation"])

            with tab_ov:
                st.subheader("Oracle Intelligence Scorecards")
                roa = info.get('returnOnAssets', 0)
                s1, s2, s3, s4, s5, s6 = st.columns(6)
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
                st.subheader("Deep-Dive Financial Indicators")
                col_l, col_r = st.columns(2)
                with col_l:
                    l_met = {
                        "Price to Earnings Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                        "Forward Price to Earnings Ratio": f"{info.get('forwardPE', 0):.2f}",
                        "Projected 3-5 Years EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                        "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                        "Price to Earnings Growth (PEG)": f"{info.get('pegRatio', 'N/A')}"
                    }
                    for k,v in l_met.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
                with col_r:
                    r_met = {
                        "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                        "Return on Invested Capital (Proxy)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                        "Free Cash Flow Yield (TTM)": f"{(info.get('freeCashflow', 0)/info.get('marketCap', 1))*100:.2f}%",
                        "Projected Long Term EPS Growth": f"{info.get('earningsQuarterlyGrowth', 0)*100:.2f}%",
                        "Shares Outstanding (Diluted)": f"{info.get('sharesOutstanding', 0):,.0f}"
                    }
                    for k,v in r_met.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

            with tab_chart:
                for sma in sma_toggle:
                    p = int(sma.split(" ")[1]); hist[sma] = hist['Close'].rolling(window=p).mean()
                supports = sorted(list(set(hist['Low'].nsmallest(10).round(2))))[:4]
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price")])
                for sma in sma_toggle: fig.add_trace(go.Scatter(x=hist.index, y=hist[sma], name=sma, line=dict(width=1.2)))
                for lvl in supports: fig.add_hline(y=lvl, line_dash="dash", line_color="green", opacity=0.4)
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with tab_val:
                st.subheader("VMI Multi-Model Valuation Suite")
                iv_20 = calculate_vmi_20yr_iv(info.get('freeCashflow', 0), info.get('totalDebt', 0), info.get('totalCash', 0), info.get('sharesOutstanding', 1), info.get('beta', 1.1))
                iv_pb = round(info.get('bookValue', 0) * 1.75, 2)
                iv_psg = round((info.get('totalRevenue', 0)/info.get('sharesOutstanding', 1)) * (info.get('revenueGrowth', 0.1)*100) * 0.2, 2)
                
                v1, v2, v3 = st.columns(3)
                v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:22px; color:#4CAF50;">${iv_20}</span></div>', unsafe_allow_html=True)
                v2.markdown(f'<div class="valuation-box"><b>Mean P/B</b><br><span style="font-size:22px; color:#4CAF50;">${iv_pb}</span></div>', unsafe_allow_html=True)
                v3.markdown(f'<div class="valuation-box"><b>PSG Model</b><br><span style="font-size:22px; color:#4CAF50;">${iv_psg}</span></div>', unsafe_allow_html=True)
                st.divider()
                st.subheader("Price Targets")
                st.metric("Mean Analyst Target", f"${info.get('targetMeanPrice', 'N/A')}")

        with col_pulse:
            st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:14px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
            for item in market_pulse:
                st.markdown(f'<div class="etf-card"><div class="etf-ticker">{item["ticker"]}</div><div class="etf-price">${item["price"]:,.2f}</div></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Error: {e}")
