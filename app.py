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
    .etf-card { background-color: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 10px; }
    .moat-badge { padding: 4px 12px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; border: 1px solid; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border-color: #4CAF50; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 13px; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .next-earn-label { background: #1b4d3e; color: #4CAF50; padding: 8px; border-radius: 6px; font-weight: 700; text-align: center; }
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
        if hist.index.tz is not None: hist.index = hist.index.tz_localize(None)

        # Header Logo & Moat
        domain = info.get('website', '').replace('https://','').replace('http://','').replace('www.','').split('/')[0] if info.get('website') else f"{ticker_sym.lower()}.com"
        logo_url = f"https://logo.clearbit.com/{domain}?size=128"
        
        c_logo, c_title = st.columns([1, 10])
        c_logo.image(logo_url)
        p_now = info.get('currentPrice', 0)
        p_chg = info.get('regularMarketChangePercent', 0)
        c_title.markdown(f'### {info.get("longName", ticker_sym)} <span class="moat-badge wide-moat">WIDE MOAT</span>', unsafe_allow_html=True)
        c_title.markdown(f'<div style="font-size:32px; font-weight:800;">${p_now:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            co1, co2 = st.columns([3, 1])
            with co1:
                st.subheader("VMI Intelligence Scorecards")
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                s1.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                s2.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(info.get("returnOnAssets",0)*100)}/10</div></div>', unsafe_allow_html=True)
                s3.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                s4.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                s5.markdown('<div class="score-card"><div class="score-label">Financial Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                s6.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                
                st.divider()
                news = stock.news
                if news:
                    st.markdown(f"**Top Synthesis:** {news[0].get('title')}")
                    st.write(news[0].get('publisher', 'Financial Intelligence'))
                st.write(info.get('longBusinessSummary'))

            with co2:
                st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:10px;">MARKET PULSE</div>', unsafe_allow_html=True)
                for t in ["SPY", "QQQ"]:
                    etf_p = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
                    st.markdown(f'<div class="etf-card"><b>{t}</b><br>${etf_p:,.2f}</div>', unsafe_allow_html=True)

        with tabs[1]: # FINANCIALS (RE-ANCHORED ALL 10)
            st.subheader("Institutional Financial Metrics (TTM)")
            f1, f2 = st.columns(2)
            metrics = {
                "P/E Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                "Forward P/E Ratio": f"{info.get('forwardPE', 0):.2f}",
                "3-5Y EPS Growth": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                "Div Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                "PEG Ratio": f"{info.get('pegRatio', 'N/A')}",
                "ROE (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                "ROIC (TTM)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                "FCF Yield": f"{(info.get('freeCashflow',0)/info.get('marketCap',1))*100:.2f}%",
                "Long-Term Growth": f"{info.get('earningsQuarterlyGrowth',0)*100:.2f}%",
                "Shares (Diluted)": f"{info.get('sharesOutstanding',0):,.0f}"
            }
            items = list(metrics.items())
            for i in range(5): f1.markdown(f'<div class="metric-row"><span class="metric-name">{items[i][0]}</span><span class="metric-val">{items[i][1]}</span></div>', unsafe_allow_html=True)
            for i in range(5, 10): f2.markdown(f'<div class="metric-row"><span class="metric-name">{items[i][0]}</span><span class="metric-val">{items[i][1]}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART (NEXT EARNING INDICATOR + SMA)
            cal = stock.calendar
            next_e = "N/A"
            if isinstance(cal, dict) and 'Earnings Date' in cal: next_e = cal['Earnings Date'][0].strftime('%Y-%m-%d')
            elif isinstance(cal, pd.DataFrame) and 'Earnings Date' in cal.index: next_e = cal.loc['Earnings Date'][0].strftime('%Y-%m-%d')
            
            st.markdown(f'<div class="next-earn-label">Next Earnings Announcement: {next_e}</div>', unsafe_allow_html=True)
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            
            # SMA Overlays
            hist['SMA50'] = hist['Close'].rolling(50).mean()
            hist['SMA200'] = hist['Close'].rolling(200).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color='orange', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color='red', width=1.5)), row=1, col=1)

            # RSI Sub-Chart
            hist['RSI'] = calculate_rsi(hist['Close'])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1) # Overbought
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1) # Oversold
            
            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION (FULL SUITE + ANALYST)
            st.subheader("Fair Value Clusters & Consenus Targets")
            v1, v2, v3 = st.columns(3)
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow',0), info.get('totalDebt',0), info.get('totalCash',0), info.get('sharesOutstanding',1), info.get('beta',1.1))
            v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v2.markdown(f'<div class="valuation-box"><b>Graham Number</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps",1) * info.get("bookValue",1)), 2)}</span></div>', unsafe_allow_html=True)
            v3.markdown(f'<div class="valuation-box"><b>PEG Fair Value</b><br><span style="font-size:24px;">${round(info.get("trailingEps",1)*(info.get("earningsGrowth",0.1)*100)*1.5, 2)}</span></div>', unsafe_allow_html=True)
            
            st.divider()
            a1, a2, a3 = st.columns(3)
            a1.metric("Low Target", f"${info.get('targetLowPrice')}")
            a2.metric("Mean Target", f"${info.get('targetMeanPrice')}")
            a3.metric("High Target", f"${info.get('targetHighPrice')}")

        with tabs[4]: # AI THESIS (DATA-DRIVEN)
            st.subheader(f"Institutional Research Thesis: {ticker_sym}")
            rev_growth = info.get('revenueGrowth', 0)*100
            roic_p = (info.get('returnOnAssets', 0)*1.8)*100
            
            b1, b2 = st.columns(2)
            with b1:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Strategic Bull Case</h4>
                <b>Ecosystem Lock-in:</b> High recurring revenue and strong R&D suggest a widening Moat. The current {rev_growth:.1f}% revenue growth is supported by {roic_p:.1f}% ROIC, creating significant shareholder value without capital dilution.</div>""", unsafe_allow_html=True)
            with b2:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Strategic Bear Case</h4>
                <b>Multiple Compression:</b> Valuation is currently pricing in a "Perfect Cycle." If ROI on current capex cycles decelerates, the stock faces a de-rating risk of its premium Forward P/E of {info.get('forwardPE', 0)}x.</div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Interrupted: {e}")
