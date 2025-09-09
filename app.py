import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import io
from PIL import Image
import cv2
import numpy as np

st.set_page_config(page_title="PDF Extractor App", layout="wide")
st.title("📄 PDF Extractor with OCR Support")

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
                continue

            # Special case: File ID + Due Date in one line
            if "Due Date:" in line and "File ID" in line:
                parts = line.split("Due Date:")
                pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
                pdf_data["Due Date"] = parts[1].strip()
                continue

            # Split only on first colon
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

    # ----------------------- OCR/Table Extraction -----------------------
    if st.button("OCR/Table Extraction to CSV"):
        st.info("🔍 Performing OCR... This may take a few seconds.")

        # Convert PDF pages to images
        try:
            pages = convert_from_bytes(uploaded_file.read())
        except Exception as e:
            st.error(f"❌ PDF to image conversion failed: {e}")
            pages = []

        if pages:
            ocr_data = {}
            for page in pages:
                # Preprocess image
                cv_image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.adaptiveThreshold(
                    gray, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )

                # OCR using pytesseract
                text = pytesseract.image_to_string(thresh)
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Split first colon as field-value
                    if ":" in line:
                        field, value = line.split(":", 1)
                        field = field.strip()
                        value = value.strip()
                        if field and value:
                            ocr_data[field] = value

            ocr_data["Filename"] = uploaded_file.name
            df_ocr = pd.DataFrame([ocr_data])
            df_ocr = df_ocr.dropna(axis=1, how="all")

            st.subheader("✅ OCR/Table Extraction Result")
            st.dataframe(df_ocr)

            csv_ocr = df_ocr.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Download CSV (OCR Extraction)",
                data=csv_ocr,
                file_name="ocr_extracted_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No pages could be converted to images. OCR extraction failed.")
