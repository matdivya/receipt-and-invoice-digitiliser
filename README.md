# Receipt and Invoice Digitizer

The Receipt and Invoice Digitizer is an OCR-based application that automates the process of extracting and managing data from receipts and invoices. It allows users to upload receipt images or PDFs, extract important billing information, store the data in a database, and visualize spending insights through analytics.

---

## Features
- Upload receipts in JPG, PNG, JPEG, and PDF formats
- Convert PDF receipts into images for processing
- Apply image preprocessing to improve OCR accuracy
- Extract key invoice details such as:
  - Vendor Name
  - Date
  - Total Amount
  - Reference Number
- Store extracted data in an SQLite database
- View invoice history in a tabular format
- Analyze expenses using interactive charts:
  - Pie Chart (Spending by Vendor)
  - Bar Chart (Total Expenses per Vendor)
  - Line Chart (Spending Over Time)

---

## Technologies Used
- Python
- Streamlit
- Tesseract OCR
- OpenCV
- SQLite
- Pandas
- Plotly
- Pillow

---

## Project Modules
1. Document Ingestion
2. OCR Processing
3. Field Extraction
4. Database Storage
5. Analytics Dashboard

---

## How to Run the Project

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
