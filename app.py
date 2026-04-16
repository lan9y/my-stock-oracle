import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import random

# --- TERMINAL CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")

# --- VMI INSTITUTIONAL CSS ---
st.markdown("""
    <style>
    .reportview-container { background: #0d1117; }
    .score-card { 
        background-color: #161b22; 
        border: 1px solid #30363d; 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .score-label { color: #8b949e; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }
    .score-value { color: #4CAF50; font-size: 28px; font-weight: 800; }
    .moat-tag { padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block; margin-top: 10px; }
    .wide-moat { background-color: #1b4d3e; color: #4CAF50; border: 1px solid #4CAF50; }
    .narrow-moat { background-color: #4d401b; color: #ff9800; border: 1px solid #ff9800; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 OraclePro™ VMI Terminal")

ticker_sym = st.sidebar.text_input("SYMBOL", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

def calculate_vmi_iv(fcf, debt, cash, shares, beta):
    rf, mrp = 0.03608, 0.02728 
    discount_rate = rf + (beta * mrp)
    g1, g2, g3 = 0.1748, 0.15, 0.04 
    total_pv = 0
    cf = fcf
    for y in range(1, 21):
        growth = g1 if y <= 5 else g2 if y <= 10 else g3
        cf *= (1 + growth)
        total_pv += cf / ((1 + discount_rate) ** y)
    return round((total_pv - debt + cash) / shares, 2) if shares > 0 else 0

if run_btn:
    with st.spinner(f'Analyzing {ticker_sym} Scorecards...'):
        try:
            stock = yf.Ticker(ticker_sym)
            time.sleep(random.uniform(1.0, 2.0)) # Polite delay
            info = stock.info
            
            if info and 'currentPrice' in info:
                # --- DATA SCRAPING FOR SCORES ---
                roa = info.get('returnOnAssets', 0)
                roe = info.get('returnOnEquity', 0)
                current_ratio = info.get('currentRatio', 1)
                rev_growth = info.get('revenueGrowth', 0)
                p_e = info.get('forwardPE', 20)

                # --- SCORE LOGIC (1-10) ---
                profit_score = int(min(roa * 100 / 1.5, 10)) if roa else 5
                growth_score = int(min(rev_growth * 100 / 2, 10)) if rev_growth else 6
                strength_score = int(min(current_ratio * 4, 10))
                predict_score = 8 if rev_growth and rev_growth > 0 else 5
                moat_score = 9 if roa > 0.12 else 6
                val_score = 10 - int(min(p_e / 10, 9))

                # --- HEADER ---
                col_h, col_m = st.columns([3, 1])
                with col_h:
                    st.header(f"{info.get('longName', ticker_sym)}")
                    st.write(f"**Sector:** {info.get('sector')} | **Industry:** {info.get('industry')}")
                with col_m:
                    moat_class = "wide-moat" if roa > 0.10 else "narrow-moat"
                    moat_text = "WIDE MOAT" if roa > 0.10 else "NARROW MOAT"
                    st.markdown(f'<div class="moat-tag {moat_class}">{moat_text}</div>', unsafe_allow_html=True)

                st.divider()

                # --- INSTITUTIONAL SCORECARDS ---
                s1, s2, s3, s4, s5, s6 = st.columns(6)
                with s1: st.markdown(f'<div class="score-card"><div class="score-label">Predictability</div><div class="score-value">{predict_score}/10</div></div>', unsafe_allow_html=True)
                with s2: st.markdown(f'<div class="score-card"><div class="score-label">Profitability</div><div class="score-value">{profit_score}/10</div></div>', unsafe_allow_html=True)
                with s3: st.markdown(f'<div class="score-card"><div class="score-label">Growth</div><div class="score-value">{growth_score}/10</div></div>', unsafe_allow_html=True)
                with s4: st.markdown(f'<div class="score-card"><div class="score-label">Oracle Moat</div><div class="score-value">{moat_score}/10</div></div>', unsafe_allow_html=True)
                with s5: st.markdown(f'<div class="score-card"><div class="score-label">Strength</div><div class="score-value">{strength_score}/10</div></div>', unsafe_allow_html=True)
                with s6: st.markdown(f'<div class="score-card"><div class="score-label">Valuation</div><div class="score-value">{val_score}/10</div></div>', unsafe_allow_html=True)

                st.divider()

                tab_ov, tab_iv = st.tabs(["📊 Business Overview", "🎯 VMI 20yr IV Model"])
                
                with tab_ov:
                    st.subheader("Institutional Segment Analysis")
                    st.write(info.get('longBusinessSummary'))
                    
                with tab_iv:
                    iv = calculate_vmi_iv(
                        info.get('freeCashflow', 0), 
                        info.get('totalDebt', 0), 
                        info.get('totalCash', 0), 
                        info.get('sharesOutstanding', 1), 
                        info.get('beta', 1.1)
                    )
                    mkt_p = info.get('currentPrice', 1)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("VMI 20yr IV", f"${iv}")
                    c2.metric("Market Price", f"${mkt_p}")
                    if mkt_p > 0:
                        mos = round(((iv - mkt_p) / mkt_p) * 100, 2)
                        c3.metric("Margin of Safety", f"{mos}%")

            else:
                st.error("Yahoo Finance connection dropped. Try once more in 60s.")

        except Exception as e:
            st.error(f"Analysis Interrupted: {e}")
