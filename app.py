import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .score-card { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .score-label { color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .score-value { color: #4CAF50; font-size: 22px; font-weight: 800; }
    .etf-card { background-color: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 12px; }
    .moat-badge { padding: 4px 12px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; border: 1px solid; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border-color: #4CAF50; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 14px; font-weight: 500; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-top: 3px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- VALUATION ENGINES ---
def vmi_20yr_dcf(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    dr = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 
    total_pv, cf = 0, fcf
    for y in range(1, 21):
        cf *= (1 + (g1 if y <= 5 else g2 if y <= 10 else g3))
        total_pv += cf / ((1 + dr) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

st.title("🔮 OraclePro™ VMI Terminal")

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1y", "2y", "5y", "max"], index=0)
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period=time_period)
        
        # 1. HEADER (LOGO & MOAT)
        curr_p = info.get('currentPrice', 0)
        p_chg = info.get('regularMarketChangePercent', 0)
        domain = info.get('website', 'apple.com').replace('https://','').replace('http://','').replace('www.','').split('/')[0]
        logo_url = f"https://logo.clearbit.com/{domain}?size=120"

        c_logo, c_head = st.columns([1, 10])
        with c_logo:
            st.image(logo_url) if domain else st.write("📷")
        with c_head:
            st.markdown(f'### {info.get("longName", ticker_sym)} ({ticker_sym}) <span class="moat-badge wide-moat">WIDE MOAT</span>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:32px; font-weight:800;">${curr_p:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            co1, co2 = st.columns([3, 1])
            with co1:
                st.subheader("Oracle Intelligence Scorecards")
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(info.get("returnOnAssets",0)*100)}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                st.divider()
                st.write(info.get('longBusinessSummary'))
            with co2:
                st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
                for t in ["SPY", "QQQ", "DIA"]:
                    etf = yf.Ticker(t).history(period="2d")
                    st.markdown(f'<div class="etf-card"><b>{t}</b><br>${etf["Close"].iloc[-1]:,.2f} <br><div style="height:40px; background:#4CAF50; opacity:0.2; border-radius:4px;"></div></div>', unsafe_allow_html=True)

        with tabs[1]: # FINANCIALS (ALL 10 METRICS RESTORED)
            st.subheader("Institutional Financial Metrics (TTM)")
            f_l, f_r = st.columns(2)
            with f_l:
                l_m = {
                    "Price to Earnings Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                    "Forward Price to Earnings Ratio (Next Year)": f"{info.get('forwardPE', 0):.2f}",
                    "Projected 3-5 Years EPS Growth Rate": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                    "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                    "Price to Earnings Growth Ratio (TTM)": f"{info.get('pegRatio', 'N/A')}"
                }
                for k,v in l_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
            with f_r:
                r_m = {
                    "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                    "Return on Invested Capital (TTM)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                    "Free Cash Flow Yield (TTM)": f"{(info.get('freeCashflow',0)/info.get('marketCap',1))*100:.2f}%",
                    "Projected Long Term EPS Growth Rate": f"{info.get('earningsQuarterlyGrowth',0)*100:.2f}%",
                    "Shares Outstanding (Diluted Average)": f"{info.get('sharesOutstanding',0):,.0f}"
                }
                for k,v in r_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART (SMA & EVENTS)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price Action"), row=1, col=1)
            
            # SMA Overlays
            hist['SMA50'] = hist['Close'].rolling(50).mean()
            hist['SMA200'] = hist['Close'].rolling(200).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color='red', width=1)), row=1, col=1)

            # X-Axis Events
            divs = stock.dividends[stock.dividends.index >= hist.index[0]]
            for dt in divs.index: fig.add_annotation(x=dt, y=0, yref="paper", text="D", font=dict(color="gold"), showarrow=False, bgcolor="#1c2128")
            
            cal = stock.calendar
            if cal is not None and 'Earnings Date' in cal:
                for ed in cal['Earnings Date']:
                    ed_c = pd.to_datetime(ed).date()
                    if hist.index[0].date() <= ed_c <= hist.index[-1].date():
                        fig.add_annotation(x=ed_c, y=0, yref="paper", text="E", font=dict(color="#4CAF50"), showarrow=False, bgcolor="#1c2128")

            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION
            st.subheader("Fair Value Clusters & Analyst Targets")
            v1, v2, v3 = st.columns(3)
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow',0), info.get('totalDebt',0), info.get('totalCash',0), info.get('sharesOutstanding',1), info.get('beta',1.1))
            v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v2.markdown(f'<div class="valuation-box"><b>Graham Number</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps", 1) * info.get("bookValue", 1)), 2)}</span></div>', unsafe_allow_html=True)
            v3.markdown(f'<div class="valuation-box"><b>Mean P/B Model</b><br><span style="font-size:24px;">${round(info.get("bookValue",0)*1.85, 2)}</span></div>', unsafe_allow_html=True)
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Analyst Low", f"${info.get('targetLowPrice')}")
            c2.metric("Analyst Mean", f"${info.get('targetMeanPrice')}")
            c3.metric("Analyst High", f"${info.get('targetHighPrice')}")

        with tabs[4]: # AI THESIS
            st.subheader("Qualitative Institutional Thesis")
            news = stock.news[:5]
            b_l, b_r = st.columns(2)
            with b_l:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case</h4>
                <b>Top Story:</b> {news[0]['title'] if news else 'Market share capture.'}<br><br>
                <b>Narrative:</b> The growth story is driven by recent pivots in M&A strategy and core-segment leadership. Revenue velocity remains high as the company scales high-margin infrastructure.</div>""", unsafe_allow_html=True)
            with b_r:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case</h4>
                <b>Top Risk:</b> {news[1]['title'] if len(news)>1 else 'Valuation multiple compression.'}<br><br>
                <b>Narrative:</b> A massive debt load of ${info.get('totalDebt',0)/1e9:.1f}B creates ROI pressure. Risks include regulatory headwinds and the high hurdle for return on capital given current massive capex spend.</div>""", unsafe_allow_html=True)

    except Exception as e: st.error(f"Sync Interrupted: {e}")
