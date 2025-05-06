
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Smart Quoting Dashboard", layout="centered")

st.title("📦 Smart Quoting Dashboard")

# 1. Upload price sheet
st.header("1. Upload SKU Price Sheet")
price_file = st.file_uploader("Upload Excel File (with MODEL, NAME IN TALLY, Qty/Box, and slab columns)", type=["xlsx"])

# 2. Optional alias mapping
st.header("2. Optional: Upload Alias Mapping")
alias_file = st.file_uploader("Upload alias mapping CSV (Alias, SKU)", type=["csv"])

quote_data = {}
alias_map = {}

if price_file:
    df = pd.read_excel(price_file)
    df.columns = df.columns.str.strip().str.lower()  # Normalize column names
    for _, row in df.iterrows():
        sku = str(row["name in tally"]).strip()
        quote_data[sku] = {
            "models": str(row["model"]).lower() if not pd.isna(row["model"]) else "",
            "qty_box": int(row["qty/box"]) if not pd.isna(row["qty/box"]) else None,
            "20pcs": row["20pcs.1"] if not pd.isna(row["20pcs.1"]) else None,
            "100pc": row["100pcs.1"] if not pd.isna(row["100pcs.1"]) else None,
            "1box": row["1 box.1"] if not pd.isna(row["1 box.1"]) else None,
            "4box": row["4 box.1"] if not pd.isna(row["4 box.1"]) else None,
        }

if alias_file:
    alias_df = pd.read_csv(alias_file)
    for _, row in alias_df.iterrows():
        alias = str(row["Alias"]).lower().strip()
        sku = str(row["SKU"]).strip()
        alias_map[alias] = sku

# 3. Paste customer message
st.header("3. Paste Customer Message")
raw_input = st.text_area("Paste customer enquiry here:", height=150)

if st.button("🧠 Generate Quote") and raw_input:
    st.subheader("📋 Quotation Output")
    lines = raw_input.lower().split('\n')
    for line in lines:
        if not line.strip():
            continue

        matched = None
        for alias, sku in alias_map.items():
            if alias in line:
                matched = sku
                break

        if not matched:
            for sku in quote_data:
                models = quote_data[sku]["models"]
                if models and any(token in line for token in models.split('/')):
                    matched = sku
                    break

        qty_match = re.search(r"(\d+)", line)
        qty = int(qty_match.group(1)) if qty_match else None

        if matched and matched in quote_data:
            slabs = {
                "20pcs": quote_data[matched].get("20pcs"),
                "100pc": quote_data[matched].get("100pc"),
                "1box": quote_data[matched].get("1box"),
                "4box": quote_data[matched].get("4box")
            }
            box_qty = quote_data[matched].get("qty_box")

            # Slab fallback
            if slabs["100pc"] is None:
                slabs["100pc"] = slabs["20pcs"]
            if slabs["1box"] is None:
                slabs["1box"] = slabs["100pc"]
            if slabs["4box"] is None:
                slabs["4box"] = slabs["1box"]

            def compute_price(qty, slabs, box_qty):
                try:
                    if qty is None or qty < 20:
                        return (None, "❌ Minimum 20 pcs")
                    if qty < 100:
                        p1 = slabs["20pcs"]
                        p2 = slabs["100pc"] if slabs["100pc"] is not None else p1
                        price = p1 + (p2 - p1) * ((qty - 20) / 80)
                    elif box_qty and qty == box_qty:
                        price = slabs["1box"]
                    elif box_qty and qty < box_qty:
                        p1 = slabs["100pc"]
                        p2 = slabs["1box"] or p1
                        price = p1 + (p2 - p1) * ((qty - 100) / (box_qty - 100))
                    elif box_qty and qty >= 4 * box_qty:
                        price = slabs["4box"]
                    elif box_qty and qty > box_qty:
                        price = slabs["1box"]
                    else:
                        price = slabs["100pc"]
                    total = round(price * qty, 2)
                    return (price, total)
                except:
                    return (None, "❌ Error in price logic")

            price, result = compute_price(qty, slabs, box_qty)
            if price:
                st.write(f"• {matched} – {qty} pcs @ ₹{price:.2f} = ₹{result:.2f}")
            else:
                st.write(f"• {matched} – {result}")
        else:
            st.write(f"• Couldn't match: '{line.strip()}'")


