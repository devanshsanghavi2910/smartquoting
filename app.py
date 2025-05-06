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
st.header("3. Paste Customer Message")
raw_input = st.text_area("Paste customer enquiry here:", height=150)

if st.button("🧠 Generate Quote") and raw_input:
    st.subheader("📋 Quotation Output")
    for line in raw_input.lower().split("\n"):
        line=line.strip()
        if not line: continue

        # 1) Try alias match
        matched = next((s for a,s in alias_map.items() if a in line), None)

        # 2) Fallback to MODEL match
        if not matched:
            for s,info in quote_data.items():
                for m in info["models"].split("/"):
                    if m and m in line:
                        matched=s
                        break
                if matched: break

        if not matched:
            st.write(f"• Couldn't match: '{line}'")
            continue

        # 3) Extract quantity: last number
        nums = re.findall(r"\d+", line)
        qty  = int(nums[-1]) if nums else None

        # 4) If 'box' in line, multiply
        box_qty = quote_data[matched]["qty_box"]
        if qty and "box" in line and box_qty:
            qty = qty * box_qty

        # 5) Prepare slab prices & fallback
        slabs = { k:quote_data[matched].get(k) for k in ("20pcs","100pc","1box","4box") }
        if slabs["100pc"] is None: slabs["100pc"] = slabs["20pcs"]
        if slabs["1box"]  is None: slabs["1box"]  = slabs["100pc"]
        if slabs["4box"]  is None: slabs["4box"]  = slabs["1box"]

        # 6) Compute price
        def compute_price(qty,slabs,box_qty):
            if qty is None or qty<20:
                return None,"❌ Minimum 20 pcs"
            if qty<100:
                p1,p2=slabs["20pcs"],slabs["100pc"]
                price = p1 + (p2-p1)*( (qty-20)/80 )
            elif box_qty and qty==box_qty:
                price=slabs["1box"]
            elif box_qty and qty<box_qty:
                p1,p2=slabs["100pc"],slabs["1box"]
                price = p1 + (p2-p1)*((qty-100)/(box_qty-100))
            elif box_qty and qty>=4*box_qty:
                price=slabs["4box"]
            elif box_qty and qty>box_qty:
                price=slabs["1box"]
            else:
                price=slabs["100pc"]
            return price, round(price*qty,2)

        unit_price, total = compute_price(qty,slabs,quote_data[matched]["qty_box"])
        if unit_price is not None:
            st.write(f"• {matched} – {qty} pcs @ ₹{unit_price:.2f} = ₹{total:.2f}")
        else:
            st.write(f"• {matched} – {total}")
