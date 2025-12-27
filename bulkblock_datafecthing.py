import requests
import pandas as pd
from io import StringIO
import os

print("🚀 NSE BULK / BLOCK CSV FETCH (APPEND MODE)")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

MASTER_FILE = os.path.join(DATA_DIR, "bulk_block_master.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/"
}

BULK_URL = "https://archives.nseindia.com/content/equities/bulk.csv"
BLOCK_URL = "https://archives.nseindia.com/content/equities/block.csv"

# ------------------------------------------------------
def detect_date_column(df):
    for col in df.columns:
        if col.lower().replace(" ", "") in ("date", "tradedate", "dt"):
            return col
    return None

# ------------------------------------------------------
def fetch_csv(url, deal_type):
    r = requests.get(url, headers=HEADERS, timeout=15)
    print(f"🔹 {deal_type} HTTP:", r.status_code)

    if r.status_code != 200 or not r.text.strip():
        print(f"❌ {deal_type} blocked / empty")
        return None

    df = pd.read_csv(StringIO(r.text))
    df["Deal Type"] = deal_type
    return df

# ------------------------------------------------------
def run():
    bulk = fetch_csv(BULK_URL, "Bulk")
    block = fetch_csv(BLOCK_URL, "Block")

    frames = [df for df in (bulk, block) if df is not None]

    if not frames:
        print("❌ No data fetched")
        return

    df_new = pd.concat(frames, ignore_index=True)

    date_col = detect_date_column(df_new)
    if not date_col:
        print("❌ Date column not found")
        return

    df_new["Trade Date"] = pd.to_datetime(
        df_new[date_col], errors="coerce"
    ).dt.date

    # ---------------- LOAD EXISTING MASTER ----------------
    if os.path.exists(MASTER_FILE):
        df_old = pd.read_csv(MASTER_FILE)
        df_old["Trade Date"] = pd.to_datetime(
            df_old["Trade Date"], errors="coerce"
        ).dt.date

        # Append only NEW dates
        latest_existing = df_old["Trade Date"].max()
        df_new = df_new[df_new["Trade Date"] > latest_existing]

        if df_new.empty:
            print("ℹ No new trade date to append")
            return

        df_final = pd.concat([df_old, df_new], ignore_index=True)

    else:
        print("📁 Master file not found. Creating new one.")
        df_final = df_new

    # Remove exact duplicates (safety)
    df_final.drop_duplicates(inplace=True)

    df_final.to_csv(MASTER_FILE, index=False)

    print("🎯 MASTER FILE UPDATED")
    print(f"📁 File: {MASTER_FILE}")
    print(f"📊 Total rows: {len(df_final)}")
    print(f"📅 Last trade date: {df_final['Trade Date'].max()}")

# ------------------------------------------------------
if __name__ == "__main__":
    run()
