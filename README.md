# 📄 PDF Field Extractor → CSV

This Streamlit app extracts **fields and values** from uploaded PDF files and exports them into a **clean CSV file**.  
It works with both **digital PDFs** and **scanned PDFs** (via OCR fallback).

---

## 🚀 Features
- Upload one or multiple PDF files
- Extracts `Field: Value` or `Field - Value` pairs
- OCR fallback for scanned PDFs
- Normalizes field names (e.g., `Due Date`, `due date`, `DUE_DATE` → `Due Date`)
- Handles missing fields with `NAN`
- Cleans & standardizes:
  - Dates → `YYYY-MM-DD`
  - Currency → numbers only
- Preview extracted data
- Download final CSV

---

## 🛠️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/pdf-field-extractor.git
   cd pdf-field-extractor
