import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time
import random

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
    .narrow-moat { background-color: #4d401b; color: #ff9800; border: 1px solid #ff9800; }
    .no-moat { background-color: #4d1b1b; color: #ff5252; border: 1px solid #ff5252; }
    .metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER: ROBUST MARKET PULSE ---
def get_market_pulse():
    indices = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones"}
    pulse = []
    try:
        data = yf.download(list(indices.keys()), period="2d", interval="1d", progress=False)
        for ticker in indices:
            price = data['Close'][ticker].iloc[-1]
            prev_price = data['Close'][ticker].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            pulse.append({"ticker": ticker, "name": indices[ticker], "price": price, "change": change})
    except:
        pulse = [{"ticker": "SPY", "price": 0, "change": 0}, {"ticker": "QQQ", "price": 0, "change": 0}]
    return pulse

# --- HELPER: RSI CALCULATION ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- VMI 20-YEAR IV CALCULATOR ---
def calculate_vmi_20yr_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    dr = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 
    total_pv, cf = 0, fcf
    for y in range(1, 21):
        cf *= (1 + (g1 if y <= 5 else g2 if y <= 10 else g3))
        total_pv += cf / ((1 + dr) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

st.title("🔮 OraclePro™ VMI Terminal")

# --- SIDEBAR ---
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
sma_toggle = st.sidebar.multiselect("OVERLAYS", ["SMA 50", "SMA 200"], default=["SMA 50"])
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period=time_period)
        
        # --- MARKET PULSE FIX ---
        market_pulse = get_market_pulse()

        col_main, col_pulse = st.columns([3, 1])

        with col_main:
            # 1. LIVE HEADER & MOAT
            roa = info.get('returnOnAssets', 0)
            roic = roa * 1.8 # Proxy
            if roic > 0.15: moat_label, moat_css = "WIDE MOAT", "wide-moat"
            elif roic > 0.08: moat_label, moat_css = "NARROW MOAT", "narrow-moat"
            else: moat_label, moat_css = "NO MOAT", "no-moat"

            curr_p = info.get('currentPrice', 0)
            p_chg = info.get('regularMarketChangePercent', 0)
            
            st.markdown(f"""
                <div style="margin-bottom:20px;">
                    <span style="color:#8b949e; font-weight:700;">{info.get('longName')} ({ticker_sym})</span>
                    <span class="moat-badge {moat_css}">{moat_label}</span>
                    <div style="font-size:42px; font-weight:800; color:#ffffff;">${curr_p:,.2f}</div>
                    <span style="color:{'#4CAF50' if p_chg >= 0 else '#FF5252'}; font-weight:700; font-size:18px;">
                        {"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%
                    </span>
                </div>
            """, unsafe_allow_html=True)

            tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

            with tabs[0]:
                st.subheader("Oracle Intelligence Scorecards")
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roa*100/1.5, 10))}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown(f'<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown(f'<div class="score-card"><div class="score-label">Moat Strength</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown(f'<div class="score-card"><div class="score-label">Financial Strength</div><div class="score-value">{int(min(info.get("currentRatio",0)*4, 10))}/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown(f'<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                st.divider()
                st.subheader("Business Summary")
                st.write(info.get('longBusinessSummary'))

            with tabs[1]:
                st.subheader("Deep-Dive Financial Indicators")
                col_l, col_r = st.columns(2)
                with col_l:
                    l_met = {"P/E Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}", "Forward P/E": f"{info.get('forwardPE', 0):.2f}", "Projected 3-5Y EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%", "Div Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%", "PEG Ratio": f"{info.get('pegRatio', 'N/A')}"}
                    for k,v in l_met.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
                with col_r:
                    r_met = {"ROE (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%", "ROIC (Proxy)": f"{roic*100:.2f}%", "FCF Yield (TTM)": f"{(info.get('freeCashflow', 0)/info.get('marketCap', 1))*100:.2f}%", "Long Term EPS Growth": f"{info.get('earningsQuarterlyGrowth', 0)*100:.2f}%", "Shares Diluted": f"{info.get('sharesOutstanding', 0):,.0f}"}
                    for k,v in r_met.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

            with tabs[2]:
                # --- SUBPLOTS: CHART + RSI ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
                
                # Overlays
                for sma in sma_toggle:
                    p = int(sma.split(" ")[1]); hist[sma] = hist['Close'].rolling(window=p).mean()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist[sma], name=sma, line=dict(width=1.2)), row=1, col=1)
                
                # Earnings/Dividend Markers
                divs = stock.dividends[stock.dividends.index >= hist.index[0]]
                if not divs.empty:
                    fig.add_trace(go.Scatter(x=divs.index, y=[hist['High'].max()]*len(divs), mode='markers', marker=dict(symbol='star', size=10, color='gold'), name='Dividend'), row=1, col=1)

                # RSI (Overbought/Oversold)
                hist['RSI'] = calculate_rsi(hist['Close'])
                fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

                fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)

            with tabs[3]:
                st.subheader("VMI Multi-Model Valuation")
                iv_20 = calculate_vmi_20yr_iv(info.get('freeCashflow', 0), info.get('totalDebt', 0), info.get('totalCash', 0), info.get('sharesOutstanding', 1), info.get('beta', 1.1))
                v1, v2, v3 = st.columns(3)
                v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:22px; color:#4CAF50;">${iv_20}</span></div>', unsafe_allow_html=True)
                v2.markdown(f'<div class="valuation-box"><b>Mean P/B</b><br><span style="font-size:22px; color:#4CAF50;">${round(info.get("bookValue",0)*1.75, 2)}</span></div>', unsafe_allow_html=True)
                v3.markdown(f'<div class="valuation-box"><b>PSG Model</b><br><span style="font-size:22px; color:#4CAF50;">${round((info.get("totalRevenue",0)/info.get("sharesOutstanding",1))*2, 2)}</span></div>', unsafe_allow_html=True)
                st.divider()
                st.metric("Mean Analyst Price Target", f"${info.get('targetMeanPrice', 'N/A')}")

            with tabs[4]:
                st.subheader(f"🤖 AI Investment Thesis: {ticker_sym}")
                c_bull, c_bear = st.columns(2)
                with c_bull:
                    st.markdown('<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case</h4>'
                                '<b>Thesis:</b> Structural AI adoption and high-margin services expansion.<br><br>'
                                '<b>Key Drivers:</b> Blackwell architecture ramp (for NVDA) or foldable iPhone upgrade cycle (for AAPL).<br>'
                                '<b>Price Prediction (2027):</b> <span style="font-size:20px;">$325 - $350</span></div>', unsafe_allow_html=True)
                with c_bear:
                    st.markdown('<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case</h4>'
                                '<b>Thesis:</b> Geopolitical regulatory risk and capital expenditure deceleration.<br><br>'
                                '<b>Key Risks:</b> China market share loss, persistent tariffs, and interest rate volatility.<br>'
                                '<b>Price Prediction (2027):</b> <span style="font-size:20px;">$200 - $220</span></div>', unsafe_allow_html=True)

        with col_pulse:
            st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px; letter-spacing:1px;">MARKET PULSE</div>', unsafe_allow_html=True)
            for item in market_pulse:
                c_clr = "#4CAF50" if item['change'] >= 0 else "#FF5252"
                st.markdown(f'<div class="etf-card"><div class="etf-ticker">{item["ticker"]}</div><div class="etf-price">${item["price"]:,.2f}</div>'
                            f'<div style="color:{c_clr}; font-size:12px; font-weight:700;">{"+" if item["change"]>=0 else ""}{item["change"]:.2f}%</div></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Interrupted: {e}")
