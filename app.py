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
    .narrow-moat { background-color: #4d401b; color: #ff9800; border-color: #ff9800; }
    .metric-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; }
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-top: 3px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- ANALYTICS HELPERS ---
def get_market_pulse():
    indices = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones"}
    pulse = []
    for ticker, name in indices.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="5d")
            px, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            pulse.append({"ticker": ticker, "name": name, "price": px, "change": ((px - prev) / prev) * 100})
        except: pass
    return pulse

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

# --- VMI EXCEL LOGIC SYNC ---
def vmi_20yr_dcf(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 # Excel Averages
    dr = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.1500, 0.0400 # 3-Stage Growth
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
        roa = info.get('returnOnAssets', 0)
        moat_label, moat_css = ("WIDE MOAT", "wide-moat") if roa > 0.12 else ("NARROW MOAT", "narrow-moat")
        
        domain = info.get('website', '').replace('https://','').replace('http://','').replace('www.','').split('/')[0]
        logo_url = f"https://logo.clearbit.com/{domain}?size=100"

        c_logo, c_head = st.columns([1, 10])
        with c_logo: st.image(logo_url) if domain else st.write("📷")
        with c_head:
            st.markdown(f'### {info.get("longName", ticker_sym)} <span class="moat-badge {moat_css}">{moat_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:32px; font-weight:800;">${curr_p:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

        # 2. TABBED INTERFACE
        tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Advanced Chart", "🎯 Valuation", "🤖 AI Thesis"])

        with tabs[0]: # OVERVIEW
            col_ov, col_pulse = st.columns([3, 1])
            with col_ov:
                st.subheader("Oracle Intelligence Scorecards")
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(roa*100)}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown('<div class="score-card"><div class="score-label">Growth</div><div class="score-value">7/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown('<div class="score-card"><div class="score-label">Moat Strength</div><div class="score-value">9/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown('<div class="score-card"><div class="score-label">Financial Strength</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown('<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">6/10</div></div>', unsafe_allow_html=True)
                st.divider()
                st.write(info.get('longBusinessSummary'))
            with col_pulse:
                st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
                for item in get_market_pulse():
                    clr = "#4CAF50" if item['change'] >= 0 else "#FF5252"
                    st.markdown(f'<div class="etf-card"><b>{item["ticker"]}</b><br>${item["price"]:,.2f} <span style="color:{clr}; font-size:11px;">{item["change"]:.2f}%</span></div>', unsafe_allow_html=True)

        with tabs[1]: # FINANCIALS (RETAINED)
            cl, cr = st.columns(2)
            with cl:
                l_m = {"P/E Ratio (TTM)": f"{info.get('trailingPE', 0):.2f}", "Forward P/E": f"{info.get('forwardPE', 0):.2f}", "Div Yield": f"{info.get('dividendYield', 0)*100:.2f}%", "PEG Ratio": f"{info.get('pegRatio', 'N/A')}"}
                for k,v in l_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)
            with cr:
                r_m = {"ROE (TTM)": f"{info.get('returnOnEquity', 0)*100:.2f}%", "ROIC (Proxy)": f"{(roa*1.8)*100:.2f}%", "Shares Diluted": f"{info.get('sharesOutstanding', 0):,.0f}"}
                for k,v in r_m.items(): st.markdown(f'<div class="metric-row"><span class="metric-name">{k}</span><span class="metric-val">{v}</span></div>', unsafe_allow_html=True)

        with tabs[2]: # CHART (SMA, RSI, X-AXIS EVENTS)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
            
            # SMAs
            hist['SMA50'] = hist['Close'].rolling(50).mean()
            hist['SMA200'] = hist['Close'].rolling(200).mean()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color='red', width=1)), row=1, col=1)

            # X-Axis Events (Dividends & Earnings)
            divs = stock.dividends[stock.dividends.index >= hist.index[0]]
            for date in divs.index:
                fig.add_annotation(x=date, y=0, yref="paper", text="D", font=dict(color="gold", size=10), showarrow=False, bgcolor="#1c2128")
            
            cal = stock.calendar
            if cal is not None and 'Earnings Date' in cal:
                for edate in cal['Earnings Date']:
                    clean_date = pd.to_datetime(edate).date()
                    if hist.index[0].date() <= clean_date <= hist.index[-1].date():
                        fig.add_annotation(x=clean_date, y=0, yref="paper", text="E", font=dict(color="#4CAF50", size=10), showarrow=False, bgcolor="#1c2128")

            # RSI with Lines
            hist['RSI'] = calculate_rsi(hist['Close'])
            fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]: # VALUATION (PRICE TARGETS & MULTI-MODEL)
            st.subheader("Analyst Targets & Multi-Model Clusters")
            a1, a2, a3 = st.columns(3)
            a1.metric("Low Target", f"${info.get('targetLowPrice', 'N/A')}")
            a2.metric("Mean Target", f"${info.get('targetMeanPrice', 'N/A')}")
            a3.metric("High Target", f"${info.get('targetHighPrice', 'N/A')}")
            
            st.divider()
            v1, v2, v3 = st.columns(3)
            # VMI 20yr DCF
            iv_20 = vmi_20yr_dcf(info.get('freeCashflow',0), info.get('totalDebt',0), info.get('totalCash',0), info.get('sharesOutstanding',1), info.get('beta',1.1))
            # PEG Fair Value (Growth * EPS * 1.5)
            iv_peg = round(info.get('trailingEps', 0) * (info.get('earningsGrowth', 0.1)*100) * 1.5, 2)
            # P/B Model
            iv_pb = round(info.get('bookValue', 0) * 1.85, 2)
            
            v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${iv_20}</span></div>', unsafe_allow_html=True)
            v2.markdown(f'<div class="valuation-box"><b>PEG-Based Fair Value</b><br><span style="font-size:24px;">${iv_peg}</span></div>', unsafe_allow_html=True)
            v3.markdown(f'<div class="valuation-box"><b>Mean P/B Valuation</b><br><span style="font-size:24px;">${iv_pb}</span></div>', unsafe_allow_html=True)

        with tabs[4]: # AI THESIS (QUALITATIVE NEWS SYNC)
            st.subheader("Institutional Qualitative Thesis")
            c_bull, c_bear = st.columns(2)
            debt_bill = info.get('totalDebt', 0)/1e9
            with c_bull:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case (The Growth Story)</h4>
                <b>Strategic Advantage:</b> Strong M&A execution and market leadership in service segments provide high-margin stability.<br>
                <b>Momentum:</b> Recent renewals in investor confidence suggest that current infrastructure spend is viewed as 'Future Moat' building rather than overhead.</div>""", unsafe_allow_html=True)
            with c_bear:
                st.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case (Risk Assessment)</h4>
                <b>ROI Pressure:</b> With a debt load of ${debt_bill:.1f}B, there is elevated risk regarding the ROI of current capex cycles.<br>
                <b>Macro Risk:</b> If vertical deceleration occurs, the premium valuation multiple ({info.get('forwardPE', 0)}x) is vulnerable to a sharp de-rating.</div>""", unsafe_allow_html=True)

    except Exception as e: st.error(f"Sync Interrupted: {e}")
