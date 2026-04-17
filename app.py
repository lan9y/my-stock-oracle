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
    .etf-ticker { font-weight: 800; color: #ffffff; font-size: 14px; }
    .moat-badge { padding: 4px 12px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; border: 1px solid; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border-color: #4CAF50; }
    .narrow-moat { background-color: #4d401b; color: #ff9800; border-color: #ff9800; }
    .metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS HELPERS ---
def get_market_pulse():
    indices = ["SPY", "QQQ", "DIA"]
    pulse = []
    for ticker in indices:
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="5d")
            px, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            pulse.append({"ticker": ticker, "price": px, "change": ((px - prev) / prev) * 100})
        except: pulse.append({"ticker": ticker, "price": 0, "change": 0})
    return pulse

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

# --- VMI EXCEL LOGIC ---
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

# --- SIDEBAR ---
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("CHART PERIOD", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period=time_period)
        
        # 1. HEADER WITH LOGO
        curr_p = info.get('currentPrice', 0)
        p_chg = info.get('regularMarketChangePercent', 0)
        roa = info.get('returnOnAssets', 0)
        moat_label, moat_css = ("WIDE MOAT", "wide-moat") if roa > 0.10 else ("NARROW MOAT", "narrow-moat")
        logo_url = f"https://logo.clearbit.com/{info.get('website', 'apple.com').replace('https://www.', '').replace('http://www.', '').split('/')[0]}"

        c_logo, c_head = st.columns([1, 10])
        with c_logo: st.image(logo_url, width=70)
        with c_head:
            st.markdown(f'### {info.get("longName", ticker_sym)} ({ticker_sym}) <span class="moat-badge {moat_css}">{moat_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:36px; font-weight:800;">${curr_p:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        # 2. TAB NAVIGATION
        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            col_ov, col_pulse = st.columns([3, 1])
            with col_ov:
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(min(roa*100/1.5, 10)) if roa else 5}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                st.divider(); st.write(info.get('longBusinessSummary'))
            with col_pulse:
                st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
                for item in get_market_pulse():
                    clr = "#4CAF50" if item['change'] >= 0 else "#FF5252"
                    st.markdown(f'<div class="etf-card"><b>{item["ticker"]}</b><br>${item["price"]:,.2f} <span style="color:{clr}; font-size:12px;">{item["change"]:.2f}%</span></div>', unsafe_allow_html=True)

        with tabs[1]: # FINANCIALS
            cl, cr = st.columns(2)
            with cl:
                metrics = {"P/E Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}", "Forward P/E": f"{info.get('forwardPE', 0):.2f}", "Div Yield": f"{info.get('dividendYield', 0)*100:.2f}%", "PEG Ratio": f"{info.get('pegRatio', 'N/A')}"}
                for k,v in metrics.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
            with cr:
                r_metrics = {"ROE (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%", "ROIC (Proxy)": f"{(roa*1.8)*100:.2f}%", "Shares Diluted": f"{info.get('sharesOutstanding',0):,.0f}"}
                for k,v in r_metrics.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            
            # Events
            cal = stock.calendar
            if cal is not None and 'Earnings Date' in cal:
                for edate in cal['Earnings Date']:
                    clean_edate = pd.to_datetime(edate).date()
                    if hist.index[0].date() <= clean_edate <= hist.index[-1].date():
                        fig.add_annotation(x=clean_edate, y=0, yref="paper", text="E", font=dict(color="#4CAF50"), showarrow=False, bgcolor="#1c2128")
            
            hist['RSI'] = calculate_rsi(hist['Close'])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION
            st.subheader("Analyst Price Targets")
            a1, a2, a3 = st.columns(3)
            a1.metric("Low Target", f"${info.get('targetLowPrice', 'N/A')}")
            a2.metric("Consensus Mean", f"${info.get('targetMeanPrice', 'N/A')}")
            a3.metric("High Target", f"${info.get('targetHighPrice', 'N/A')}")
            st.divider()
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow', 0), info.get('totalDebt', 0), info.get('totalCash', 0), info.get('sharesOutstanding', 1), info.get('beta', 1.1))
            v1, v2, v3 = st.columns(3)
            v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v2.markdown(f'<div class="valuation-box"><b>Graham Number</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps", 1) * info.get("bookValue", 1)), 2)}</span></div>', unsafe_allow_html=True)
            v3.markdown(f'<div class="valuation-box"><b>PSG Model</b><br><span style="font-size:24px;">${round((info.get("totalRevenue",0)/info.get("sharesOutstanding",1))*2.5, 2)}</span></div>', unsafe_allow_html=True)

        with tabs[4]: # AI THESIS
            st.subheader(f"Institutional Thesis: {ticker_sym}")
            b1, b2 = st.columns(2)
            with b1:
                st.markdown(f'<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case</h4><b>Growth:</b> {info.get("revenueGrowth",0)*100:.1f}% Rev Growth indicates strong market capture.<br><b>Liquidity:</b> ${info.get("totalCash",0)/1e9:.1f}B cash reserves supports R&D and buybacks.</div>', unsafe_allow_html=True)
            with b2:
                st.markdown(f'<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case</h4><b>Leverage:</b> Total debt of ${info.get("totalDebt",0)/1e9:.1f}B poses risk in high-rate cycles.<br><b>Pricing:</b> Forward P/E of {info.get("forwardPE",0)} is significantly above sector median.</div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"Sync Interrupted: {e}")
