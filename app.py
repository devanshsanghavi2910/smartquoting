# quoting_dashboard_streamlit.py
# This is your Streamlit quoting assistant

import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Smart Quoting Dashboard", layout="centered")
st.title("🧾 Smart Quoting Assistant")

# --- Upload SKU Master ---
st.header("1. Upload Your SKU Price Sheet")
file = st.file_uploader("Upload Excel (.xlsx) with SKU & Pricing", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    st.success("✅ File uploaded and loaded.")

    # Normalize column names
    df.columns = [col.strip() for col in df.columns]

    # Create a dictionary for quoting
    quote_data = {}
    for _, row in df.iterrows():
        sku_name = str(row['NAME IN TALLY']).strip()
        models = str(row['MODEL']).strip().lower()
        qty_box = row.get('Qty/ Box', None)
        quote_data[sku_name] = {
            "models": models,
            "qty_box": qty_box,
            "20pcs": row.get("20pcs.1", None),
            "100pc": row.get("100pc.1", None),
            "1box": row.get("1 Box.1", None),
            "4box": row.get("4 Box.1", None),
        }

    # --- Alias Mapping (Optional) ---
    st.header("2. Optional: Upload Alias Mapping")
    alias_file = st.file_uploader("Upload alias mapping CSV (Alias, SKU)", type=["csv"])
    alias_map = {}
    if alias_file:
        alias_df = pd.read_csv(alias_file)
        for _, row in alias_df.iterrows():
            alias_map[str(row['Alias']).strip().lower()] = str(row['SKU']).strip()
        st.success("✅ Alias map loaded.")

    # --- Customer Message ---
    st.header("3. Paste Customer Message")
    raw_input = st.text_area("Paste customer enquiry here:", height=200)

    def compute_price(qty, slabs, box_qty):
        try:
            qty = int(qty)
            if qty < 20:
                return (None, "❌ Minimum 20 pcs")
            if qty < 100:
                p1, p2 = slabs['20pcs'], slabs['100pc'] or slabs['20pcs']
                price = p1 + (p2 - p1) * ((qty - 20) / 80)
            elif box_qty and qty == box_qty:
                price = slabs['1box'] or slabs['100pc']
            elif box_qty and qty < box_qty:
                p1, p2 = slabs['100pc'], slabs['1box'] or slabs['100pc']
                price = p1 + (p2 - p1) * ((qty - 100) / (box_qty - 100))
            elif box_qty and qty >= 4 * box_qty:
                price = slabs['4box'] or slabs['1box'] or slabs['100pc']
            elif box_qty and qty > box_qty:
                price = slabs['1box'] or slabs['100pc']
            else:
                price = slabs['100pc']
            total = round(price * qty, 2)
            return (price, total)
        except:
            return (None, "❌ Error in price logic")

    # --- Process Input ---
    if st.button("🧠 Generate Quote") and raw_input:
        st.subheader("📋 Quotation Output")
        lines = raw_input.lower().split('\n')
        for line in lines:
            matched = None
            for alias, sku in alias_map.items():
                if alias in line:
                    matched = sku
                    break
            if not matched:
                for sku in quote_data:
                    if any(token in line for token in quote_data[sku]["models"].split('/')):
                        matched = sku
                        break
            qty_match = re.search(r"(\\d+)", line)
if qty_match:
    qty = int(qty_match.group(1))
else:
    qty = None

            if matched and matched in quote_data:
                slabs = {
                    "20pcs": quote_data[matched].get("20pcs"),
                    "100pc": quote_data[matched].get("100pc"),
                    "1box": quote_data[matched].get("1box"),
                    "4box": quote_data[matched].get("4box")
                }
                box_qty = quote_data[matched].get("qty_box")
                price, result = compute_price(qty, slabs, box_qty)
                if price:
                    st.write(f"• {matched} – {qty} pcs @ ₹{price:.2f} = ₹{result:.2f}")
                else:
                    st.write(f"• {matched} – {result}")
            else:
                st.write(f"• Couldn't match: '{line.strip()}'")
