import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
# Replace with your FRESH Key
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t" 
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ VMI Terminal")

ticker = st.sidebar.text_input("SYMBOL", value="INTC").upper().strip()
run_btn = st.sidebar.button("EXECUTE ANALYSIS")

# --- VMI 20-YEAR IV CALCULATOR ---
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
    with st.spinner('Scavenging available data...'):
        try:
            # 1. THE QUOTE CALL (Most likely to be open)
            q = requests.get(f"{BASE_URL}/quote/{ticker}?apikey={API_KEY}").json()
            time.sleep(2.0)
            
            # 2. THE RATIOS CALL
            r = requests.get(f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}").json()
            time.sleep(2.0)
            
            # 3. THE METRICS CALL
            m = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}").json()

            if q and isinstance(q, list):
                stock = q[0]
                ratio = r[0] if r else {}
                metric = m[0] if m else {}
                
                # --- UI OVERVIEW ---
                st.header(f"{stock.get('name')} ({ticker})")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Market Price", f"${stock.get('price')}")
                
                # --- VMI CALCULATION ---
                fcf = metric.get('freeCashFlowTTM', 0)
                debt = metric.get('netDebtTTM', 0)
                cash = metric.get('cashAndShortTermInvestmentsTTM', 0)
                shares = metric.get('numberOfSharesTTM', 1)
                
                # Fallback to sector-average beta if restricted
                beta = 1.2 
                
                iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                col2.metric("VMI 20yr IV", f"${iv}")
                
                if stock.get('price'):
                    mos = round(((iv - stock.get('price')) / stock.get('price')) * 100, 2)
                    col3.metric("Margin of Safety", f"{mos}%")

                st.divider()
                st.subheader("Moat & Profitability Indicators")
                c_a, c_b = st.columns(2)
                c_a.write(f"**ROIC (TTM):** {round(ratio.get('returnOnCapitalEmployedTTM', 0)*100, 2)}%")
                c_b.write(f"**Gross Margin:** {round(ratio.get('grossProfitMarginTTM', 0)*100, 2)}%")
                
                if ratio.get('returnOnCapitalEmployedTTM', 0) > 0.15:
                    st.success("🛡️ WIDE MOAT DETECTED (High ROIC)")
                else:
                    st.warning("⚠️ NARROW/NO MOAT (Standard ROIC)")

            else:
                st.error(f"403 ERROR: {ticker} is fully locked for free users. Try INTC, CSCO, or WMT.")

        except Exception as e:
            st.error(f"Sync Interrupted: {e}")
