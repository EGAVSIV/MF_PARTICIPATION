import streamlit as st
import pandas as pd
import requests
from datetime import date

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="Mutual Fund Bulk Deal Intelligence",
    layout="wide",
    page_icon="🏦"
)

st.title("🏦 Mutual Fund Bulk / Block Deal Flow – NSE")
st.caption("Identify Mutual Fund Accumulation & Exit using NSE disclosures")

# ============================================================
# DATE FILTER (SIDEBAR)
# ============================================================
st.sidebar.header("📅 Trade Date Filter")

selected_date = st.sidebar.date_input(
    "Select Trade Date",
    value=date.today()
)

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
    # Pre-hit homepage (mandatory)
    s.get("https://www.nseindia.com", timeout=5)
    return s

# ============================================================
# FETCH BULK + BLOCK DEAL DATA
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
        if not data:
            continue

        df = pd.DataFrame(data)
        df["Deal Type"] = deal_type
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Convert NSE date
    df["Trade Date"] = pd.to_datetime(
        df["tradeDate"], errors="coerce"
    ).dt.date

    return df

# ============================================================
# MUTUAL FUND IDENTIFICATION
# ============================================================
def is_mutual_fund(name: str) -> bool:
    if not isinstance(name, str):
        return False

    keywords = [
        "MUTUAL FUND", "MF", "TRUSTEE", "AMC",
        "ASSET MANAGEMENT", "SBI", "HDFC", "ICICI",
        "AXIS", "KOTAK", "NIPPON", "DSP",
        "UTI", "MIRAE", "ADITYA", "INVESCO"
    ]

    name = name.upper()
    return any(k in name for k in keywords)

# ============================================================
# CLASSIFY MF FLOW
# ============================================================
def classify_flow(row):
    buyer_mf = is_mutual_fund(row.get("clientName"))
    seller_mf = is_mutual_fund(row.get("sellClientName"))

    if buyer_mf and not seller_mf:
        return "🟢 MF ACCUMULATION"
    elif seller_mf and not buyer_mf:
        return "🔴 MF EXIT"
    else:
        return "⚪ IGNORE"

# ============================================================
# LOAD & FILTER DATA
# ============================================================
df = fetch_bulk_block()

df = df[df["Trade Date"] == selected_date]

if df.empty:
    st.warning(f"No Bulk / Block Deals found for {selected_date}")
    st.stop()

df["MF Signal"] = df.apply(classify_flow, axis=1)

# Keep only actionable signals
action_df = df[df["MF Signal"] != "⚪ IGNORE"].copy()

# ============================================================
# SUMMARY METRICS
# ============================================================
st.subheader("📊 Mutual Fund Activity Summary")

c1, c2 = st.columns(2)
c1.metric(
    "🟢 MF Accumulation Trades",
    (action_df["MF Signal"] == "🟢 MF ACCUMULATION").sum()
)
c2.metric(
    "🔴 MF Exit Trades",
    (action_df["MF Signal"] == "🔴 MF EXIT").sum()
)

# ============================================================
# DISPLAY TABLE
# ============================================================
st.subheader("📋 Actionable Mutual Fund Transactions")

display_cols = {
    "symbol": "Stock",
    "Deal Type": "Deal Type",
    "clientName": "Buyer",
    "sellClientName": "Seller",
    "quantity": "Quantity",
    "price": "Price",
    "MF Signal": "MF Signal"
}

table = action_df[list(display_cols.keys())].rename(columns=display_cols)

st.dataframe(
    table.sort_values("MF Signal"),
    use_container_width=True,
    height=520
)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
---
### 🔎 Interpretation Guide
🟢 **MF ACCUMULATION** → Strong institutional buying (Bullish)  
🔴 **MF EXIT** → Institutional distribution (Bearish)  
⚪ **Ignored** → MF↔MF or Non-MF↔Non-MF (Noise)

Designed for **NSE positional & swing traders**
""")
