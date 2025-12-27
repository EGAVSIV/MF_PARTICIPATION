import streamlit as st
import pandas as pd
import re

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Mutual Fund Bulk / Block Analysis",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Mutual Fund Bulk / Block Deal Analysis")
st.caption("⚡ Optimized | CSV-based | Fast")

DATA_FILE = "data/bulk_block_master.csv"

# =====================================================
# OFFICIAL MF NAMES (CLEAN)
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
    "TATA","TAURUS","THE WEALTH COMPANY","TRUST MUTUAL",
    "UNIFI","UNION","UTI","WHITEOAK CAPITAL","ZERODHA",
    "General Insurance","GIC RE","LIC","LIFE INSURANCE",
    "Max Financial","Star Health","Punjab National Bank",
    "PNB", "Canara","IDBI","Union Bank","Indian Bank",
    "The New India Assurance",
]

MF_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(x) for x in MF_KEYWORDS) + r")\b",
    flags=re.IGNORECASE
)

# =====================================================
# LOAD + PREPARE DATA (CACHED)
# =====================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_data():
    df = pd.read_csv(DATA_FILE)

    df.columns = df.columns.str.strip()

    # Date normalization
    df["Trade Date"] = pd.to_datetime(
        df["Trade Date"], errors="coerce"
    ).dt.date

    # Uppercase once
    df["Client Name"] = df["Client Name"].astype(str).str.upper()
    df["Buy/Sell"] = df["Buy/Sell"].astype(str).str.upper()

    # 🔥 VECTORISED MF DETECTION
    is_mf = df["Client Name"].str.contains(MF_REGEX, na=False)

    df["MF Signal"] = "⚪ IGNORE"
    df.loc[is_mf & (df["Buy/Sell"] == "BUY"), "MF Signal"] = "🟢 MF ACCUMULATION"
    df.loc[is_mf & (df["Buy/Sell"] == "SELL"), "MF Signal"] = "🔴 MF EXIT"

    return df

df = load_data()

if df.empty:
    st.error("No data available")
    st.stop()

# =====================================================
# SIDEBAR FILTER
# =====================================================
st.sidebar.header("📅 Date Filter")

min_d, max_d = df["Trade Date"].min(), df["Trade Date"].max()

start, end = st.sidebar.date_input(
    "Select Date Range",
    value=(min_d, max_d),
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
# STOCK SUMMARY
# =====================================================
st.subheader("📊 Stock-wise MF Activity")

summary = (
    df.groupby(["Symbol", "MF Signal"], as_index=False)
      .agg({"Quantity Traded": "sum"})
      .sort_values("Quantity Traded", ascending=False)
)

st.dataframe(summary, use_container_width=True, height=350)

# =====================================================
# DETAILS
# =====================================================
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

st.caption("🚀 Optimized for Streamlit Cloud – no row-wise apply")
