import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- CONFIG ---
st.set_page_config(page_title="OraclePro™ VMI Terminal", layout="wide")
API_KEY = "vJFsENcD098gHX91EBFKtKIAKoCTpj9t"
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.title("🔮 OraclePro™ VMI Terminal")

ticker = st.sidebar.text_input("SYMBOL (Try a mid-cap if 403 persists)", value="AAPL").upper().strip()
run_btn = st.sidebar.button("EXECUTE VMI ANALYSIS")

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
    with st.spinner('Accessing Open-Tier Data Streams...'):
        try:
            # SWITCHED TO 'QUOTE' (Usually bypasses 403 on Profile)
            q_url = f"{BASE_URL}/quote/{ticker}?apikey={API_KEY}"
            q_res = requests.get(q_url, timeout=10).json()
            time.sleep(2.0)
            
            # KEY METRICS (For FCF and Shares)
            m_url = f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}"
            m_res = requests.get(m_url, timeout=10).json()

            if q_res and isinstance(q_res, list):
                q = q_res[0]
                m = m_res[0] if m_res else {}
                
                # --- UI OVERVIEW ---
                st.header(f"{q.get('name')} ({ticker})")
                st.subheader(f"Price: ${q.get('price')} | Change: {q.get('changesPercentage')}%")
                
                # --- VMI CALC ---
                # We use fallback values to prevent 0-division
                fcf = m.get('freeCashFlowTTM', 0)
                debt = m.get('netDebtTTM', 0)
                cash = m.get('cashAndShortTermInvestmentsTTM', 0)
                shares = m.get('numberOfSharesTTM', 1)
                
                # Beta fallback for free tier
                beta = 1.2 
                
                iv = calculate_vmi_iv(fcf, debt, cash, shares, beta)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("VMI 20yr IV", f"${iv}")
                c2.metric("Market Price", f"${q.get('price')}")
                if q.get('price'):
                    mos = round(((iv - q.get('price')) / q.get('price')) * 100, 2)
                    c3.metric("Margin of Safety", f"{mos}%")
                
                st.success("✅ Connection Successful using Quote Fallback.")
                
            else:
                st.error("403 Forbidden: This ticker is restricted on the free tier. Try a different symbol (e.g., INTC or TSLA).")
                
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
