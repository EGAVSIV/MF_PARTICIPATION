import streamlit as st
import pandas as pd
from datetime import date

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Mutual Fund Bulk / Block Analysis",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Mutual Fund Bulk / Block Deal Analysis")
st.caption("CSV-based | Fast | No NSE dependency")

# =====================================================
# LOAD MASTER DATA
# =====================================================
DATA_FILE = "data/bulk_block_master.csv"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(DATA_FILE)

    # Normalize column names (safe)
    df.columns = df.columns.str.strip()

    # Ensure Trade Date exists
    if "Trade Date" not in df.columns:
        # fallback safety (should not happen)
        for c in df.columns:
            if c.lower().replace(" ", "") in ("date", "tradedate", "dt"):
                df["Trade Date"] = pd.to_datetime(df[c], errors="coerce").dt.date
                break
    else:
        df["Trade Date"] = pd.to_datetime(df["Trade Date"], errors="coerce").dt.date

    return df

df = load_data()

if df.empty:
    st.error("No data found in bulk_block_master.csv")
    st.stop()

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("📅 Filters")

min_date = df["Trade Date"].min()
max_date = df["Trade Date"].max()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) != 2:
    st.warning("Please select a valid date range")
    st.stop()

start_date, end_date = date_range

# =====================================================
# FILTER DATA
# =====================================================
df = df[
    (df["Trade Date"] >= start_date) &
    (df["Trade Date"] <= end_date)
].copy()

# =====================================================
# MUTUAL FUND IDENTIFICATION
# =====================================================
MF_KEYWORDS = ["360 ONE","ABAKKUS","ADITYA BIRLA SUN LIFE","ANGEL ONE",
    "AXIS","BAJAJ FINSERV","BANDHAN",
    "BANK OF INDIA","BARODA BNP PARIBAS","CANARA ROBECO","CAPITALMIND","CHOICE","DSP","EDELWEISS","FRANKLIN TEMPLETON","GROWW","HDFC",
    "HELIOS","HSBC","ICICI PRUDENTIAL","IDBI","INVESCO","JM FINANCIAL","JIO BLACKROCK","KOTAK","LIC","MAHINDRA MANULIFE","MIRAE ASSET","MOTILAL OSWAL","N J","NAVI","NIPPON INDIA","OLD BRIDGE",
    "PGIM INDIA","PPFAS","QUANT","QUANTUM","SAMCO",
    "SBI","SHRIRAM","SUNDARAM","TATA","TAURUS","THE WEALTH COMPANY","TRUST","UNIFI","UNION","UTI","WHITEOAK CAPITAL","ZERODHA"
]

def is_mutual_fund(name):
    if not isinstance(name, str):
        return False
    name = name.upper()
    return any(k in name for k in MF_KEYWORDS)

# =====================================================
# CLASSIFY MF FLOW
# =====================================================
def classify(row):
    buyer = row.get("Client Name", "")
    side = str(row.get("Buy/Sell", "")).upper()

    if is_mutual_fund(buyer) and side == "BUY":
        return "🟢 MF ACCUMULATION"
    if is_mutual_fund(buyer) and side == "SELL":
        return "🔴 MF EXIT"
    return "⚪ IGNORE"

df["MF Signal"] = df.apply(classify, axis=1)

# Keep only actionable
df_action = df[df["MF Signal"] != "⚪ IGNORE"].copy()

# =====================================================
# SUMMARY METRICS
# =====================================================
c1, c2, c3 = st.columns(3)

c1.metric("🟢 MF Accumulation Trades",
          (df_action["MF Signal"] == "🟢 MF ACCUMULATION").sum())

c2.metric("🔴 MF Exit Trades",
          (df_action["MF Signal"] == "🔴 MF EXIT").sum())

c3.metric("📊 Total Records", len(df_action))

# =====================================================
# STOCK-WISE SUMMARY
# =====================================================
st.subheader("📊 Stock-wise Mutual Fund Activity")

stock_summary = (
    df_action
    .groupby(["Symbol", "MF Signal"])
    .agg({
        "Quantity Traded": "sum"
    })
    .reset_index()
    .sort_values("Quantity Traded", ascending=False)
)

st.dataframe(stock_summary, use_container_width=True, height=400)

# =====================================================
# DETAILED TABLE
# =====================================================
st.subheader("📋 Detailed Transactions")

show_cols = [
    "Trade Date", "Symbol", "Security Name",
    "Client Name", "Buy/Sell",
    "Quantity Traded",
    "Trade Price / Wght. Avg. Price",
    "MF Signal"
]

available_cols = [c for c in show_cols if c in df_action.columns]

st.dataframe(
    df_action[available_cols].sort_values("Trade Date", ascending=False),
    use_container_width=True,
    height=500
)

# =====================================================
# FOOTER
# =====================================================
st.markdown("""
---
🟢 **MF Accumulation** → Mutual Fund buying (bullish)  
🔴 **MF Exit** → Mutual Fund selling (bearish)  

Data Source: NSE Bulk & Block Deals (CSV Archive)  
Designed for **positional & swing analysis**
""")
