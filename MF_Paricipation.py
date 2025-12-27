import streamlit as st
import pandas as pd
import requests
from datetime import date
import re

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="Mutual Fund Bulk Deal Intelligence",
    layout="wide",
    page_icon="🏦"
)

st.title("🏦 Mutual Fund Bulk Deal Flow – NSE")
st.caption("Detect Accumulation & Exit from NSE Bulk / Block Deals")

# ============================================================
# NSE SAFE SESSION
# ============================================================
def nse_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/"
    })
    s.get("https://www.nseindia.com", timeout=5)
    return s

# ============================================================
# FETCH BULK + BLOCK DEALS
# ============================================================
@st.cache_data(ttl=300)
def fetch_bulk_block():
    s = nse_session()

    urls = {
        "Bulk": "https://www.nseindia.com/api/bulk-deals",
        "Block": "https://www.nseindia.com/api/block-deals"
    }

    frames = []
    for deal_type, url in urls.items():
        r = s.get(url, timeout=10)
        if r.status_code != 200:
            continue

        data = r.json().get("data", [])
        df = pd.DataFrame(data)
        if df.empty:
            continue

        df["Deal Type"] = deal_type
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["Trade Date"] = pd.to_datetime(df["tradeDate"]).dt.date
    return df[df["Trade Date"] == date.today()]

# ============================================================
# MUTUAL FUND IDENTIFICATION
# ============================================================
def is_mutual_fund(name: str) -> bool:
    if not isinstance(name, str):
        return False
    keywords = [
        "MUTUAL FUND", "MF", "TRUSTEE", "ASSET MANAGEMENT",
        "AMC", "INVESCO", "SBI", "HDFC", "ICICI", "AXIS",
        "KOTAK", "NIPPON", "DSP", "UTI", "MIRAE", "ADITYA"
    ]
    name = name.upper()
    return any(k in name for k in keywords)

# ============================================================
# CLASSIFICATION LOGIC
# ============================================================
def classify(row):
    buyer_mf = is_mutual_fund(row["clientName"])
    seller_mf = is_mutual_fund(row["sellClientName"])

    if buyer_mf and not seller_mf:
        return "🟢 MF ACCUMULATION"
    elif seller_mf and not buyer_mf:
        return "🔴 MF EXIT"
    else:
        return "⚪ IGNORE"

# ============================================================
# LOAD DATA
# ============================================================
df = fetch_bulk_block()

if df.empty:
    st.warning("No Bulk / Block Deals found for today.")
    st.stop()

df["MF Signal"] = df.apply(classify, axis=1)

# ============================================================
# FILTER ACTIONABLE FLOWS
# ============================================================
action_df = df[df["MF Signal"] != "⚪ IGNORE"].copy()

# ============================================================
# DISPLAY SUMMARY
# ============================================================
st.subheader("📊 Today’s Mutual Fund Activity Summary")

c1, c2 = st.columns(2)
c1.metric("🟢 MF Accumulation Trades", (action_df["MF Signal"] == "🟢 MF ACCUMULATION").sum())
c2.metric("🔴 MF Exit Trades", (action_df["MF Signal"] == "🔴 MF EXIT").sum())

# ============================================================
# DISPLAY TABLE
# ============================================================
st.subheader("📋 Actionable MF Transactions")

display_cols = {
    "symbol": "Stock",
    "Deal Type": "Deal",
    "clientName": "Buyer",
    "sellClientName": "Seller",
    "quantity": "Qty",
    "price": "Price",
    "MF Signal": "MF Signal"
}

table = action_df[list(display_cols.keys())].rename(columns=display_cols)

st.dataframe(
    table.sort_values("MF Signal"),
    use_container_width=True,
    height=500
)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
---
**Interpretation Guide**

🟢 **MF ACCUMULATION** → Strong institutional buying (Bullish)  
🔴 **MF EXIT** → Distribution / exit signal (Bearish)  
⚪ **Ignored** → Internal MF churn or non-institutional  

Designed for **NSE positional & swing traders**
""")
