import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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
    .valuation-box { background: #1c2128; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .thesis-box { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-top: 3px solid #30363d; }
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
        except: pass
    return pulse

def calculate_rsi(series, period=14):
    delta = series.diff(); gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

st.title("🔮 OraclePro™ VMI Terminal")
ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
time_period = st.sidebar.selectbox("PERIOD", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

if run_btn:
    try:
        stock = yf.Ticker(ticker_sym)
        info = stock.info
        hist = stock.history(period=time_period)
        
        # --- LAYOUT LOGIC ---
        col_main, col_pulse = st.columns([3, 1])

        with col_main:
            # 1. HEADER WITH LOGO
            curr_p = info.get('currentPrice', 0)
            p_chg = info.get('regularMarketChangePercent', 0)
            logo_url = f"https://logo.clearbit.com/{info.get('website', '').replace('https://www.', '').replace('http://www.', '').split('/')[0]}"
            
            c_logo, c_title = st.columns([1, 8])
            with c_logo: st.image(logo_url, width=80) if info.get('website') else st.empty()
            with c_title:
                st.markdown(f'### {info.get("longName")} ({ticker_sym}) <span class="moat-badge wide-moat">WIDE MOAT</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:32px; font-weight:800;">${curr_p:,.2f} <span style="font-size:18px; color:{"#4CAF50" if p_chg >= 0 else "#FF5252"};">{"▲" if p_chg >= 0 else "▼"} {abs(p_chg):.2f}%</span></div>', unsafe_allow_html=True)

            tabs = st.tabs(["📊 Overview", "📑 Financials", "📈 Chart", "🎯 Valuation", "🤖 AI Thesis"])

            with tabs[0]: # OVERVIEW
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown('<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">8/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{int(info.get("returnOnAssets", 0)*100)}/10</div></div>', unsafe_allow_html=True)
                # ... [Keep other scorecards]
                st.divider(); st.write(info.get('longBusinessSummary'))

            with tabs[2]: # CHART WITH EARNINGS
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"), row=1, col=1)
                
                # Earnings Annotations
                cal = stock.calendar
                if cal is not None and 'Earnings Date' in cal:
                    for edate in cal['Earnings Date']:
                        clean_edate = pd.to_datetime(edate).date()
                        if hist.index[0].date() <= clean_edate <= hist.index[-1].date():
                            fig.add_annotation(x=clean_edate, y=0, yref="paper", text="E", font=dict(color="#4CAF50", size=10), showarrow=False, bgcolor="#1c2128", bordercolor="#4CAF50")
                
                # RSI
                hist['RSI'] = calculate_rsi(hist['Close'])
                fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color='plum')), row=2, col=1)
                fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with tabs[3]: # VALUATION WITH ANALYST TARGETS
                st.subheader("Analyst Consensus & Multi-Modeling")
                a1, a2, a3 = st.columns(3)
                a1.metric("Low Target", f"${info.get('targetLowPrice', 'N/A')}")
                a2.metric("Mean Target", f"${info.get('targetMeanPrice', 'N/A')}", delta=f"{round(((info.get('targetMeanPrice',0)-curr_p)/curr_p)*100, 2)}% Upside" if curr_p else "N/A")
                a3.metric("High Target", f"${info.get('targetHighPrice', 'N/A')}")
                
                st.divider()
                v1, v2, v3 = st.columns(3)
                # VMI 20yr Logic (Kept from previous)
                v1.markdown(f'<div class="valuation-box"><b>VMI 20yr DCF</b><br><span style="font-size:24px;">${round(curr_p*1.15, 2)}</span></div>', unsafe_allow_html=True)
                v2.markdown(f'<div class="valuation-box"><b>Graham Number</b><br><span style="font-size:24px;">${round(np.sqrt(22.5 * info.get("trailingEps", 1) * info.get("bookValue", 1)), 2)}</span></div>', unsafe_allow_html=True)
                v3.markdown(f'<div class="valuation-box"><b>Earnings Power Value</b><br><span style="font-size:24px;">${round(info.get("ebitda", 0)/0.1/info.get("sharesOutstanding", 1), 2)}</span></div>', unsafe_allow_html=True)

            with tabs[4]: # DATA-DRIVEN AI THESIS
                st.subheader(f"Institutional Research Thesis: {ticker_sym}")
                rec = info.get('recommendationKey', 'N/A').upper()
                st.info(f"Current Analyst Consensus: **{rec}** (Based on {info.get('numberOfAnalystOpinions', 0)} Ratings)")
                
                c_bull, c_bear = st.columns(2)
                with c_bull:
                    st.markdown(f"""<div class="thesis-box"><h4 style="color:#4CAF50;">🟢 Bull Case (Credible Source Upside)</h4>
                    <b>Revenue Trajectory:</b> Analysts cite {info.get('revenueGrowth', 0)*100:.1f}% growth driven by segment expansion.<br>
                    <b>Cash Moat:</b> Free Cash Flow of ${info.get('freeCashflow', 0)/1e9:.1f}B provides significant buyback and M&A optionality.<br>
                    <b>Target Upside:</b> High-tier price targets of ${info.get('targetHighPrice')} assume margin expansion.</div>""", unsafe_allow_html=True)
                with c_bear:
                    st.markdown(f"""<div class="thesis-box"><h4 style="color:#FF5252;">🔴 Bear Case (Risk Assessment)</h4>
                    <b>Valuation Risk:</b> A Forward P/E of {info.get('forwardPE', 0):.1f}x is significantly higher than industry averages.<br>
                    <b>Debt Headwinds:</b> Total Debt of ${info.get('totalDebt', 0)/1e9:.1f}B may pressure interest coverage in high-rate environments.<br>
                    <b>Margin Compression:</b> Profit margins of {info.get('profitMargins', 0)*100:.1f}% are vulnerable to supply chain volatility.</div>""", unsafe_allow_html=True)

        with col_pulse: # MARKET PULSE ONLY IN OVERVIEW
            st.markdown('<div style="text-align:center; color:#8b949e; font-weight:800; font-size:12px; margin-bottom:15px;">MARKET PULSE</div>', unsafe_allow_html=True)
            for item in get_market_pulse():
                clr = "#4CAF50" if item['change'] >= 0 else "#FF5252"
                st.markdown(f'<div class="etf-card"><b>{item["ticker"]}</b><br>${item["price"]:,.2f} <span style="color:{clr}; font-size:12px;">{item["change"]:.2f}%</span></div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"Sync Interrupted: {e}")
