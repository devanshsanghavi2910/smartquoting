import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Smart Quoting Dashboard", layout="centered")
st.title("📦 Smart Quoting Dashboard")

# 1. Upload SKU Price Sheet
st.header("1. Upload SKU Price Sheet")
price_file = st.file_uploader(
    "Upload Excel File (with MODEL, NAME IN TALLY, Qty/Box, and slab columns)",
    type=["xlsx"]
)

# 2. Optional: Upload Alias Mapping
st.header("2. Optional: Upload Alias Mapping")
alias_file = st.file_uploader("Upload alias mapping CSV (Alias, SKU)", type=["csv"])

quote_data = {}
alias_map = {}

if price_file:
    df = pd.read_excel(price_file)
    df.columns = df.columns.str.strip().str.lower()
    # auto-detect the Qty/Box column
    qty_box_col = next((c for c in df.columns if "qty" in c and "box" in c), None)

    for _, row in df.iterrows():
        sku = str(row.get("name in tally","")).strip()
        quote_data[sku] = {
            "models": str(row.get("model","")).lower(),
            "qty_box": int(row[qty_box_col]) if qty_box_col and not pd.isna(row[qty_box_col]) else None,
            "20pcs":   row.get("20pcs.1"),
            "100pc":   row.get("100pcs.1"),
            "1box":    row.get("1 box.1"),
            "4box":    row.get("4 box.1"),
        }

if alias_file:
    alias_df = pd.read_csv(alias_file)
    for _, row in alias_df.iterrows():
        alias = str(row.get("Alias","")).lower().strip()
        sku   = str(row.get("SKU","")).strip()
        if alias and sku:
            alias_map[alias] = sku

# 3. Paste customer message
st.header("3. Paste Cust
