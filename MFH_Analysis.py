import streamlit as st
import pandas as pd
import re
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Mutual Fund Bulk / Block Analysis",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Mutual Fund Bulk / Block Deal Analysis")
st.caption("⚡ Parquet-based | Cloud-safe | No cache deadlocks")

DATA_FILE = "data/bulk_block_master.parquet"

# =====================================================
# SIDEBAR CONTROLS
# =====================================================
st.sidebar.header("⚙️ Controls")

if not os.path.exists(DATA_FILE):
    st.error("❌ Parquet file not found")
    st.stop()

load_btn = st.sidebar.button("📥 Load MF Bulk/Block Data")

if not load_btn:
    st.info("👈 Click **Load MF Bulk/Block Data** to start")
    st.stop()

# =====================================================
# MF KEYWORDS (RAW LIST ONLY)
# =====================================================
MF_KEYWORDS = [
    "360 ONE","ABAKKUS","ADITYA BIRLA SUN LIFE","ANGEL ONE",
    "AXIS","BAJAJ FINSERV","BANDHAN","BANK OF INDIA",
    "BARODA BNP PARIBAS","CANARA ROBECO","CAPITALMIND",
    "CHOICE","DSP","EDELWEISS","FRANKLIN TEMPLETON",
    "GROWW","HDFC","HELIOS","HSBC","ICICI PRUDENTIAL",
    "IDBI","INVESCO","JM FINANCIAL","JIO BLACKROCK",
    "KOTAK","LIC","MAHINDRA MANULIFE","MIRAE ASSET",
    "MOTILAL OSWAL","N J","NAVI","NIPPON INDIA",
    "OLD BRIDGE","PGIM INDIA","PPFAS","QUANT",
    "QUANTUM","SAMCO","SBI","SHRIRAM","SUNDARAM",
    "TATA","TAURUS","THE WEALTH COMPANY","TRUSTMUTUAL",
    "UNIFI","UNION","UTI","WHITEOAK CAPITAL","ZERODHA",
    "General Insurance","GIC RE","LIFE INSURANCE",
    "Max Financial","Star Health","Punjab National Bank",
    "PNB","Canara","Union Bank","Indian Bank",
    "The New India Assurance",
]

# =====================================================
# LOAD DATA (NO CACHE)
# =====================================================
with st.spinner("Loading parquet..."):
    df = pd.read_parquet(DATA_FILE)

df.columns = df.columns.str.strip()

df["Trade Date"] = pd.to_datetime(
    df["Trade Date"], errors="coerce"
).dt.date

df["Client Name"] = df["Client Name"].astype(str).str.upper()
df["Buy/Sell"] = df["Buy/Sell"].astype(str).str.upper()

# Compile regex INSIDE runtime (CRITICAL)
mf_pattern = r"\b(" + "|".join(map(re.escape, MF_KEYWORDS)) + r")\b"
is_mf = df["Client Name"].str.contains(mf_pattern, case=False, regex=True, na=False)

df["MF Signal"] = "⚪ IGNORE"
df.loc[is_mf & (df["Buy/Sell"] == "BUY"), "MF Signal"] = "🟢 MF ACCUMULATION"
df.loc[is_mf & (df["Buy/Sell"] == "SELL"), "MF Signal"] = "🔴 MF EXIT"

# =====================================================
# DATE FILTER
# =====================================================
st.sidebar.header("📅 Date Filter")

min_d, max_d = df["Trade Date"].min(), df["Trade Date"].max()

start, end = st.sidebar.date_input(
    "Select Date Range",
    value=(max_d, max_d),
    min_value=min_d,
    max_value=max_d
)

df = df[
    (df["Trade Date"] >= start) &
    (df["Trade Date"] <= end) &
    (df["MF Signal"] != "⚪ IGNORE")
]

# =====================================================
# METRICS
# =====================================================
c1, c2, c3 = st.columns(3)
c1.metric("🟢 MF Accumulation", (df["MF Signal"] == "🟢 MF ACCUMULATION").sum())
c2.metric("🔴 MF Exit", (df["MF Signal"] == "🔴 MF EXIT").sum())
c3.metric("📊 Records", len(df))

# =====================================================
# TABLES
# =====================================================
st.subheader("📊 Stock-wise MF Activity")

summary = (
    df.groupby(["Symbol", "MF Signal"], as_index=False)
      .agg({"Quantity Traded": "sum"})
      .sort_values("Quantity Traded", ascending=False)
)

st.dataframe(summary, use_container_width=True, height=350)

st.subheader("📋 Detailed Transactions")

st.dataframe(
    df[[
        "Trade Date","Symbol","Security Name",
        "Client Name","Buy/Sell",
        "Quantity Traded",
        "Trade Price / Wght. Avg. Price",
        "MF Signal"
    ]].sort_values("Trade Date", ascending=False),
    use_container_width=True,
    height=450
)

st.caption("✅ Stable on Streamlit Cloud | No cache | No deadlocks")
