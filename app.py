import streamlit as st
import os
import re
import sqlite3
import pandas as pd
import plotly.express as px
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Receipt & Invoice Digitizer", layout="wide")

# =========================
# SESSION STATE
# =========================
if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = None

# =========================
# TESSERACT PATH
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# FOLDERS
# =========================
os.makedirs("uploads", exist_ok=True)

# =========================
# DATABASE
# =========================
def init_db():
    conn = sqlite3.connect("invoices.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_no TEXT,
            vendor TEXT,
            date TEXT,
            total REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_invoice(ref, vendor, date, total):
    conn = sqlite3.connect("invoices.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO invoices (reference_no, vendor, date, total) VALUES (?, ?, ?, ?)",
        (ref, vendor, date, total)
    )
    conn.commit()
    conn.close()

def fetch_all_records():
    conn = sqlite3.connect("invoices.db")
    df = pd.read_sql("SELECT * FROM invoices", conn)
    conn.close()
    return df

init_db()

# =========================
# HELPER FUNCTIONS
# =========================
def normalize_vendor(v):
    if not v:
        return "Unknown"
    v = v.lower()
    v = re.sub(r"[^a-z ]", "", v)
    return v.strip().title()

def extract_date(text):
    patterns = [
        r"\d{2}[/-]\d{2}[/-]\d{4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}\s+[A-Za-z]{3,}\s+\d{4}",
        r"[A-Za-z]{3,}\s+\d{2},\s*\d{4}"
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(0)
    return "Unknown"

def extract_total_amount(text):
    candidates = []
    keywords = ["total", "amount", "payable", "grand"]

    for line in text.split("\n"):
        if any(k in line.lower() for k in keywords):
            nums = re.findall(r"[\₹Rs\.]?\s*([\d,]+(?:\.\d{1,2})?)", line)
            for n in nums:
                try:
                    candidates.append(float(n.replace(",", "")))
                except:
                    pass

    if not candidates:
        nums = re.findall(r"[\d,]+\.\d{2}", text)
        for n in nums:
            try:
                candidates.append(float(n.replace(",", "")))
            except:
                pass

    return max(candidates) if candidates else 0.0

# =========================
# TITLE
# =========================
st.title("🧾 Receipt & Invoice Digitizer")
st.caption("Upload receipts, extract data, and view analytics")

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📁 Vault & Upload",
    "📜 History",
    "📊 Analytics Dashboard"
])

# =========================
# TAB 1: UPLOAD + OCR
# =========================
with tab1:
    st.subheader("Upload Receipt")

    uploaded_file = st.file_uploader(
        "Upload Image or PDF",
        type=["jpg", "jpeg", "png", "pdf"]
    )

    image = None
    processed_img = None

    if uploaded_file:
        path = os.path.join("uploads", uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.type == "application/pdf":
            pages = convert_from_path(path, dpi=300)
            image = pages[0]
            st.success("PDF uploaded (first page used)")
        else:
            image = Image.open(path)
            st.success("Image uploaded successfully")

    if image is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.image(image, caption="Original Image", width=300)

        with col2:
            st.markdown("### Preprocessing Options")

            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

            resize_factor = st.slider(
                "Resize factor",
                min_value=1.0,
                max_value=2.0,
                step=0.1,
                value=1.2
            )

            denoise = st.checkbox("Apply Denoise")

            img = cv2.resize(
                img,
                None,
                fx=resize_factor,
                fy=resize_factor,
                interpolation=cv2.INTER_CUBIC
            )

            if denoise:
                img = cv2.GaussianBlur(img, (5, 5), 0)

            processed_img = img

            st.image(
                processed_img,
                caption="Processed Image (for OCR)",
                width=300
            )

    if processed_img is not None and st.button("🔍 Run OCR"):
        text = pytesseract.image_to_string(processed_img, config="--oem 3 --psm 6")

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        vendor = normalize_vendor(lines[0]) if lines else "Unknown"
        date = extract_date(text)
        total = extract_total_amount(text)

        reference_no = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        st.session_state.ocr_data = {
            "reference_no": reference_no,
            "vendor": vendor,
            "date": date,
            "total": total
        }

    if st.session_state.ocr_data:
        d = st.session_state.ocr_data

        st.markdown("### 📌 Extracted Details")
        st.write(d)

        if d["total"] == 0:
            st.warning("⚠ Total amount not detected properly.")

        if st.button("💾 Save to Database"):
            if d["total"] > 0:
                insert_invoice(
                    d["reference_no"],
                    d["vendor"],
                    d["date"],
                    d["total"]
                )
                st.success("Invoice saved successfully ✔")
                st.session_state.ocr_data = None
            else:
                st.error("Cannot save invoice with zero total.")

# =========================
# TAB 2: HISTORY
# =========================
with tab2:
    st.subheader("📜 Invoice History")
    df = fetch_all_records()
    st.dataframe(df, use_container_width=True)

# =========================
# TAB 3: ANALYTICS
# =========================
with tab3:
    st.subheader("📊 Spending Insights")

    df = fetch_all_records()
    df = df[df["total"] > 0]

    if df.empty:
        st.warning("No valid records found.")
    else:
        df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")

        vendor_group = df.groupby("vendor", as_index=False)["total"].sum()

        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(
                px.pie(
                    vendor_group,
                    names="vendor",
                    values="total",
                    title="Spending by Vendor"
                ),
                use_container_width=True
            )

        with col2:
            st.plotly_chart(
                px.bar(
                    vendor_group,
                    x="vendor",
                    y="total",
                    title="Total Expenses per Vendor"
                ),
                use_container_width=True
            )

        st.markdown("### 📈 Spending Over Time")
        time_df = df.dropna(subset=["date_parsed"])
        st.plotly_chart(
            px.line(
                time_df,
                x="date_parsed",
                y="total",
                markers=True,
                title="Spending Over Time"
            ),
            use_container_width=True
        )
