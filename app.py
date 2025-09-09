import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image

st.set_page_config(page_title="PDF Extractor App", layout="wide")
st.title("📄 PDF Extractor with OCR/Table Support (No OpenCV)")

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

    # ----------------------- OCR/Table Extraction (No ':' Condition) -----------------------
    if st.button("OCR/Table Extraction to CSV"):
        st.info("🔍 Performing OCR... This may take a few seconds.")

        try:
            pages = convert_from_bytes(uploaded_file.read())
        except Exception as e:
            st.error(f"❌ PDF to image conversion failed: {e}")
            pages = []

        if pages:
            ocr_data = {}
            for page_num, page in enumerate(pages, start=1):
                # Convert page to grayscale
                gray_image = page.convert("L")
                # OCR text
                text = pytesseract.image_to_string(gray_image)
                # Split lines
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                
                # For OCR/Table extraction, treat every **line as field-value pair**:
                # The first word or phrase until a space is field, rest is value
                for line in lines:
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        field, value = parts
                    else:
                        field = parts[0]
                        value = ""
                    # Only store if field is not empty
                    if field:
                        # If field already exists, append with separator
                        if field in ocr_data:
                            ocr_data[field] += " | " + value
                        else:
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
