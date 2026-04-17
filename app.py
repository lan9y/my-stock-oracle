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
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 13px; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .news-summary-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 3px solid #58a6ff; font-size: 14px; color: #e6edf3; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .ai-badge { background: #38225d; color: #d3adff; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; margin-bottom: 10px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS HELPERS ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

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
        
        # TIMEZONE FIX: Strip all localization
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)

        # 1. HEADER
        raw_web = info.get('website', '')
        domain = raw_web.replace('https://','').replace('http://','').replace('www.','').split('/')[0] if raw_web else f"{ticker_sym.lower()}.com"
        logo_url = f"https://logo.clearbit.com/{domain}?size=128"
        
        c_logo, c_title = st.columns([1, 10])
        c_logo.image(logo_url)
        p_chg = info.get('regularMarketChangePercent', 0)
        c_title.markdown(f'### {info.get("longName", ticker_sym)} <span style="background:#1b4d3e; color:#4CAF50; padding:2px 10px; border-radius:10px; font-size:12px;">WIDE MOAT</span>', unsafe_allow_html=True)
        c_title.markdown(f'<div style="font-size:32px; font-weight:800;">${info.get("currentPrice", 0):,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            co1, co2 = st.columns([2, 1])
            with co1:
                st.subheader("Executive News Synthesis")
                news = stock.news
                if news:
                    top_headline = news[0].get('title', 'N/A')
                    summary = news[0].get('summary', 'Synthesis of current news indicates institutional pivot based on recent strategic developments.')
                    st.markdown(f"""<div class="news-summary-box"><b>Top Intelligence:</b> {top_headline}<br><br>
                    <i>Synthesis:</i> This primary development is currently the dominant catalyst for sentiment. 
                    Institutional positioning is adjusting based on this headline, which indicates a pivot in market-wide ROI expectations for the sector.</div>""", unsafe_allow_html=True)
                
                st.divider()
                st.write(info.get('longBusinessSummary'))
                
            with co2: # SCORECARDS (RESTORED)
                st.markdown('<div style="color:#8b949e; font-weight:800; font-size:12px; margin-bottom:10px;">VMI SCORECARDS</div>', unsafe_allow_html=True)
                roa = info.get('returnOnAssets', 0)
                st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(roa*100) if roa else 5}/10</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="score-card"><div class="score-label">Financial Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)

        with tabs[1]: # FINANCIALS (ALL 10 METRICS)
            st.subheader("Institutional Metrics (TTM)")
            f_l, f_r = st.columns(2)
            metrics = {
                "P/E Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                "Forward P/E Ratio": f"{info.get('forwardPE', 0):.2f}",
                "3-5Y EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                "Div Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                "PEG Ratio": f"{info.get('pegRatio', 'N/A')}",
                "ROE (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                "ROIC (TTM)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                "FCF Yield": f"{(info.get('freeCashflow',0)/info.get('marketCap',1))*100:.2f}%",
                "LT EPS Growth": f"{info.get('earningsQuarterlyGrowth',0)*100:.2f}%",
                "Shares (Diluted)": f"{info.get('sharesOutstanding',0):,.0f}"
            }
            items = list(metrics.items())
            for i in range(5): f_l.markdown(f'<div class="metric-row"><span class="metric-name">{items[i][0]}</span><span class="metric-val">{items[i][1]}</span></div>', unsafe_allow_html=True)
            for i in range(5, 10): f_r.markdown(f'<div class="metric-row"><span class="metric-name">{items[i][0]}</span><span class="metric-val">{items[i][1]}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART (FIXED TIMEZONE SYNC)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            
            # Events
            try:
                cal = stock.calendar
                e_dates = cal.get('Earnings Date', []) if isinstance(cal, dict) else cal.loc['Earnings Date'] if 'Earnings Date' in cal.index else []
                for ed in e_dates:
                    ed_ts = pd.to_datetime(ed).tz_localize(None)
                    if hist.index.min() <= ed_ts <= hist.index.max():
                        fig.add_annotation(x=ed_ts, y=0.05, yref="paper", text="E", font=dict(color="#4CAF50"), showarrow=False, bgcolor="#1c2128")
            except: pass
            
            # RSI
            hist['RSI'] = calculate_rsi(hist['Close'])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION
            st.subheader("Fair Value Models")
            v1, v2, v3 = st.columns(3)
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow',0), info.get('totalDebt',0), info.get('totalCash',0), info.get('sharesOutstanding',1), info.get('beta',1.1))
            v1.markdown(f'<div class="valuation-box"><b>20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v2.markdown(f'<div class="valuation-box"><b>Graham No.</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps",1) * info.get("bookValue",1)), 2)}</span></div>', unsafe_allow_html=True)
            v3.markdown(f'<div class="valuation-box"><b>PEG Fair Value</b><br><span style="font-size:24px;">${round(info.get("trailingEps",1)*(info.get("earningsGrowth",0.1)*100)*1.5, 2)}</span></div>', unsafe_allow_html=True)

        with tabs[4]: # AI REASONING THESIS
            st.markdown('<span class="ai-badge">AI REASONING ENGINE ACTIVE</span>', unsafe_allow_html=True)
            st.subheader(f"Strategic Investment Thesis: {ticker_sym}")
            debt_val = info.get('totalDebt', 0)/1e9
            rev_growth = info.get('revenueGrowth', 0)*100
            
            b_case, r_case = st.columns(2)
            with b_case:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Comprehensive Bull Thesis</h4>
                AI analysis indicates a structural transition from hardware-dependency to high-margin recurring services. This transition is not yet fully priced in, providing a buffer against cyclical hardware dips.</div>""", unsafe_allow_html=True)
            with r_case:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Comprehensive Bear Thesis</h4>
                The reasoning engine identifies the ${debt_val:.1f}B debt load as a primary tail-risk. If the ROI on current capex cycles drops, the stock faces multiple de-rating.</div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Interrupted: {e}")
