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

# 2. Optional alias mapping
st.header("2. Optional: Upload Alias Mapping")
alias_file = st.file_uploader("Upload alias mapping CSV (Alias, SKU)", type=["csv"])

quote_data = {}
alias_map = {}

# Load price sheet
if price_file:
    df = pd.read_excel(price_file)
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    # Find the Qty/Box column (whatever its exact name)
    qty_box_col = next((c for c in df.columns if "qty" in c and "box" in c), None)

    for _, row in df.iterrows():
        sku = str(row.get("name in tally", "")).strip()
        quote_data[sku] = {
            "models": str(row.get("model", "")).lower(),
            "qty_box": int(row[qty_box_col]) if qty_box_col and not pd.isna(row[qty_box_col]) else None,
            "20pcs": row.get("20pcs.1"),
            "100pc": row.get("100pcs.1"),
            "1box": row.get("1 box.1"),
            "4box": row.get("4 box.1"),
        }

# Load aliases
if alias_file:
    alias_df = pd.read_csv(alias_file)
    for _, row in alias_df.iterrows():
        alias = str(row.get("Alias", "")).lower().strip()
        sku   = str(row.get("SKU", "")).strip()
        if alias and sku:
            alias_map[alias] = sku

# 3. Paste customer message
st.header("3. Paste Customer Message")
raw_input = st.text_area("Paste customer enquiry here:", height=150)

if st.button("🧠 Generate Quote") and raw_input:
    st.subheader("📋 Quotation Output")
    lines = raw_input.lower().split("\n")

    for line in lines:
        if not line.strip():
            continue

        # 1) Alias match
        matched = next((sku for alias, sku in alias_map.items() if alias in line), None)

        # 2) Model-based match fallback
        if not matched:
            for sku, info in quote_data.items():
                models = info["models"]
                if models and any(tok in line for tok in models.split("/")):
                    matched = sku
                    break

        # 3) Quantity extraction
        qty = None
        box_match = re.search(r"(\d+)\s*box(?:es)?", line)
        pc_match  = re.search(r"(\d+)\s*(?:pcs?|pieces?)", line)

        if matched and matched in quote_data:
            box_qty = quote_data[matched]["qty_box"]

            if box_match and box_qty:
                qty = int(box_match.group(1)) * box_qty
            elif pc_match:
                qty = int(pc_match.group(1))
            else:
                # last resort: grab the LAST number
                all_nums = re.findall(r"\d+", line)
                qty = int(all_nums[-1]) if all_nums else None

            # Gather slabs and apply fallbacks
            slabs = {
                "20pcs": quote_data[matched].get("20pcs"),
                "100pc": quote_data[matched].get("100pc"),
                "1box": quote_data[matched].get("1box"),
                "4box": quote_data[matched].get("4box"),
            }
            if slabs["100pc"] is None:
                slabs["100pc"] = slabs["20pcs"]
            if slabs["1box"] is None:
                slabs["1box"] = slabs["100pc"]
            if slabs["4box"] is None:
                slabs["4box"] = slabs["1box"]

            # Pricing logic
            def compute_price(qty, slabs, box_qty):
                try:
                    if qty is None or qty < 20:
                        return (None, "❌ Minimum 20 pcs")
                    if qty < 100:
                        p1 = slabs["20pcs"]
                        p2 = slabs["100pc"]
                        price = p1 + (p2 - p1) * ((qty - 20) / 80)
                    elif box_qty and qty == box_qty:
                        price = slabs["1box"]
                    elif box_qty and qty < box_qty:
                        p1 = slabs["100pc"]
                        p2 = slabs["1box"]
                        price = p1 + (p2 - p1) * ((qty - 100) / (box_qty - 100))
                    elif box_qty and qty >= 4 * box_qty:
                        price = slabs["4box"]
                    elif box_qty and qty > box_qty:
                        price = slabs["1box"]
                    else:
                        price = slabs["100pc"]
                    return (price, round(price * qty, 2))
                except:
                    return (None, "❌ Error in price logic")

            unit_price, total = compute_price(qty, slabs, box_qty)
            if unit_price is not None:
                st.write(f"• {matched} – {qty} pcs @ ₹{unit_price:.2f} = ₹{total:.2f}")
            else:
                st.write(f"• {matched} – {total}")
        else:
            st.write(f"• Couldn't match: '{line.strip()}'")

