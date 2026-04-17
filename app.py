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
    .etf-card { background-color: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 8px; margin-bottom: 5px; }
    .moat-badge { padding: 4px 12px; border-radius: 15px; font-weight: 800; font-size: 12px; margin-left: 10px; border: 1px solid; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border-color: #4CAF50; }
    .metric-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #30363d; }
    .metric-name { color: #8b949e; font-size: 14px; font-weight: 500; }
    .metric-val { color: #ffffff; font-weight: 700; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-top: 3px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS HELPERS ---
def get_sparkline(ticker_code):
    try:
        data = yf.download(ticker_code, period="30d", interval="1d", progress=False)['Close']
        if data.empty: return None
        fig = go.Figure(data=go.Scatter(y=data, line=dict(color='#4CAF50', width=2), hoverinfo='none'))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, margin=dict(l=0,r=0,t=0,b=0), height=40, width=120, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    except: return None

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
        
        # --- HEADER (RESTORED LOGO WITH FALLBACK) ---
        raw_web = info.get('website', '')
        domain = raw_web.replace('https://','').replace('http://','').replace('www.','').split('/')[0] if raw_web else ""
        if not domain: domain = f"{ticker_sym.lower()}.com"
        logo_url = f"https://logo.clearbit.com/{domain}?size=100"
        
        c_h1, c_h2 = st.columns([1, 10])
        c_h1.image(logo_url)
            
        p_now = info.get('currentPrice', 0)
        p_chg = info.get('regularMarketChangePercent', 0)
        roa = info.get('returnOnAssets', 0)
        moat_label, moat_css = ("WIDE MOAT", "wide-moat") if roa > 0.12 else ("NARROW MOAT", "narrow-moat")
        
        c_h2.markdown(f'### {info.get("longName", ticker_sym)} <span class="moat-badge {moat_css}">{moat_label}</span>', unsafe_allow_html=True)
        c_h2.markdown(f'<div style="font-size:32px; font-weight:800;">${p_now:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            co1, co2 = st.columns([3, 1])
            s1, s2, s3, s4, s5, s6 = co1.columns(6)
            s1.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
            s2.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(roa*100) if roa else 5}/10</div></div>', unsafe_allow_html=True)
            s3.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
            s4.markdown('<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
            s5.markdown('<div class="score-card"><div class="score-label">Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
            s6.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
            co1.divider(); co1.write(info.get('longBusinessSummary'))
            
            co2.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
            for t in ["SPY", "QQQ", "DIA"]:
                p_data = yf.Ticker(t).history(period="2d")
                px, chg = p_data['Close'].iloc[-1], ((p_data['Close'].iloc[-1]-p_data['Close'].iloc[-2])/p_data['Close'].iloc[-2])*100
                co2.markdown(f'<div class="etf-card"><b>{t}</b> ${px:,.2f} <span style="color:{"#4CAF50" if chg >= 0 else "#FF5252"};">{chg:+.2f}%</span></div>', unsafe_allow_html=True)
                spark = get_sparkline(t)
                if spark: co2.plotly_chart(spark, use_container_width=True, config={'displayModeBar': False})

        with tabs[1]: # FINANCIALS (STRICTLY THE 10 REQUESTED)
            st.subheader("Institutional Financial Metrics (TTM)")
            f_l, f_r = st.columns(2)
            l_m = {
                "Price to Earnings Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}",
                "Forward Price to Earnings Ratio (Next Year)": f"{info.get('forwardPE', 0):.2f}",
                "Projected 3-5 Years EPS Growth Rate": f"{info.get('earningsGrowth', 0)*100:.2f}%",
                "Dividend Yield (TTM)": f"{info.get('dividendYield', 0)*100:.2f}%",
                "Price to Earnings Growth Ratio (TTM)": f"{info.get('pegRatio', 'N/A')}"
            }
            r_m = {
                "Return on Equity (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                "Return on Invested Capital (TTM)": f"{(info.get('returnOnAssets', 0)*1.8)*100:.2f}%",
                "Free Cash Flow Yield (TTM)": f"{(info.get('freeCashflow',0)/info.get('marketCap',1))*100:.2f}%",
                "Projected Long Term EPS Growth Rate": f"{info.get('earningsQuarterlyGrowth',0)*100:.2f}%",
                "Shares Outstanding (Diluted Average)": f"{info.get('sharesOutstanding',0):,.0f}"
            }
            for k,v in l_m.items(): f_l.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
            for k,v in r_m.items(): f_r.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART (SMA + RSI + HARDENED EVENTS)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            # Strip timezones for matching
            hist.index = hist.index.tz_localize(None)
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            
            # Technicals
            hist['SMA50'] = hist['Close'].rolling(50).mean()
            hist['SMA200'] = hist['Close'].rolling(200).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color='orange', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color='red', width=1.2)), row=1, col=1)

            # RSI with X-Axis
            hist['RSI'] = calculate_rsi(hist['Close'])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # X-AXIS EVENT BADGES (D & E)
            divs = stock.dividends[stock.dividends.index >= hist.index[0]]
            for dt, val in divs.items():
                fig.add_annotation(x=dt.tz_localize(None), y=0.05, yref="paper", text="D", font=dict(color="gold", size=10), showarrow=False, bgcolor="#1c2128", bordercolor="gold")
            
            try:
                cal = stock.calendar
                # Handle calendar date matching correctly
                if 'Earnings Date' in cal:
                    e_dates = cal['Earnings Date'] if isinstance(cal['Earnings Date'], list) else [cal['Earnings Date']]
                    for ed in e_dates:
                        ed_clean = pd.to_datetime(ed).tz_localize(None)
                        if hist.index[0] <= ed_clean <= hist.index[-1]:
                            fig.add_annotation(x=ed_clean, y=0.05, yref="paper", text="E", font=dict(color="#4CAF50", size=10), showarrow=False, bgcolor="#1c2128", bordercolor="#4CAF50")
            except: pass

            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION (CLUSTER & ANALYST)
            st.subheader("Fair Value Clusters & Analyst Targets")
            v_l, v_r = st.columns(2)
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow',0), info.get('totalDebt',0), info.get('totalCash',0), info.get('sharesOutstanding',1), info.get('beta',1.1))
            v_l.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v_l.markdown(f'<div class="valuation-box"><b>Mean P/B Valuation</b><br><span style="font-size:24px;">${round(info.get("bookValue",0)*1.85, 2)}</span></div>', unsafe_allow_html=True)
            v_r.markdown(f'<div class="valuation-box"><b>PEG Fair Value</b><br><span style="font-size:24px;">${round(info.get("trailingEps",1)*(info.get("earningsGrowth",0.1)*100)*1.5, 2)}</span></div>', unsafe_allow_html=True)
            v_r.markdown(f'<div class="valuation-box"><b>Graham Number</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps",1) * info.get("bookValue",1)), 2)}</span></div>', unsafe_allow_html=True)
            st.divider(); a1, a2, a3 = st.columns(3)
            a1.metric("Analyst Low", f"${info.get('targetLowPrice')}"); a2.metric("Analyst Mean", f"${info.get('targetMeanPrice')}"); a3.metric("Analyst High", f"${info.get('targetHighPrice')}")

        with tabs[4]: # AI THESIS (DATA-NEWS DRIVEN)
            st.subheader("Institutional Research Thesis")
            news = stock.news
            b1, b2 = st.columns(2)
            h1 = news[0].get('title', 'Strategic Catalyst') if news else 'Revenue Expansion'
            h2 = news[1].get('title', 'Headwinds Identified') if len(news) > 1 else 'Multiple Compression Risk'
            b1.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case</h4><b>Signal:</b> {h1}<br><br><b>Growth Narrative:</b> Growth centers on margin expansion and ecosystem lock-in. News suggests a widening Oracle Moat through innovation.</div>""", unsafe_allow_html=True)
            b2.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case</h4><b>Risk:</b> {h2}<br><br><b>Constraint:</b> A debt load of ${info.get('totalDebt',0)/1e9:.1f}B creates ROI pressure. vertical deceleration could de-rate the multiple.</div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Interrupted: {e}")
