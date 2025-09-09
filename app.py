import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import re

st.set_page_config(page_title="PDF Extractor App", layout="wide")
st.title("📄 PDF Extractor with OCR Table Support")

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    st.subheader("📄 Uploaded PDF Preview")
    st.write(f"Filename: {uploaded_file.name}")
    st.write(f"File size: {uploaded_file.size / 1024:.2f} KB")

    # ----------------------- Direct PDF Extraction -----------------------
    if st.button("Direct PDF Extraction"):
        pdf_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"

        pdf_data = {}
        for line in pdf_text.splitlines():
            line = line.strip()
            if ":" not in line:
                continue  # Only split on lines with colon

            # Special case: File ID + Due Date in one line
            if "Due Date:" in line and "File ID" in line:
                parts = line.split("Due Date:")
                pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
                pdf_data["Due Date"] = parts[1].strip()
                continue

            field, value = line.split(":", 1)
            field = field.strip()
            value = value.strip()
            if field and value:
                pdf_data[field] = value

        pdf_data["Filename"] = uploaded_file.name
        df_direct = pd.DataFrame([pdf_data])
        df_direct = df_direct.dropna(axis=1, how="all")

        st.subheader("✅ Direct PDF Extraction Result")
        st.dataframe(df_direct)

        csv_direct = df_direct.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Download CSV (Direct Extraction)",
            data=csv_direct,
            file_name="direct_extracted_data.csv",
            mime="text/csv"
        )

    # ----------------------- OCR Table Extraction -----------------------
    if st.button("OCR Table Extraction to CSV"):
        st.info("🔍 Performing OCR Table extraction... This may take a few seconds.")

        try:
            pages = convert_from_bytes(uploaded_file.read())
        except Exception as e:
            st.error(f"❌ PDF to image conversion failed: {e}")
            pages = []

        if pages:
            all_rows = []

            for i, page in enumerate(pages):
                st.image(page, caption=f"Page {i+1}", use_column_width=True)

                gray_image = page.convert("L")
                # OCR using pytesseract with PSM 6 (assume uniform block of text)
                text = pytesseract.image_to_string(gray_image, config="--psm 6")
                lines = [line.strip() for line in text.splitlines() if line.strip()]

                if len(lines) < 2:
                    continue  # Skip pages without table-like content

                # Assume first line = headers
                headers = re.split(r'\s{2,}', lines[0])
                for line in lines[1:]:
                    values = re.split(r'\s{2,}', line)
                    row = {}
                    for idx, header in enumerate(headers):
                        row[header] = values[idx] if idx < len(values) else ""
                    all_rows.append(row)

            if all_rows:
                df_ocr = pd.DataFrame(all_rows)
                df_ocr["Filename"] = uploaded_file.name
                df_ocr = df_ocr.dropna(axis=1, how="all")

                st.subheader("✅ OCR Table Extraction Result")
                st.dataframe(df_ocr)

                csv_ocr = df_ocr.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Download CSV (OCR Table Extraction)",
                    data=csv_ocr,
                    file_name="ocr_table_extracted_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No table-like content detected in OCR output. Try enhancing PDF quality or using higher-res scans.")
