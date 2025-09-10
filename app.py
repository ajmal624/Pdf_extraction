import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO
import re

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.subheader("📖 PDF Preview")
    try:
        uploaded_file.seek(0)
        pages = convert_from_bytes(uploaded_file.read())
        for i, page in enumerate(pages):
            st.image(page, caption=f"Page {i+1}", use_column_width=True)
    except Exception as e:
        st.error(f"Failed to render PDF: {e}")

    st.write("---")
    st.subheader("⚡ Extraction Options")

    col1, col2 = st.columns(2)

    # -------------------- Direct PDF Extraction to CSV --------------------
    with col1:
        if st.button("Direct PDF Extraction to CSV"):
            uploaded_file.seek(0)
            pdf_text = ""
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pdf_text += text + "\n"
            except Exception as e:
                st.error(f"Error reading PDF: {e}")
                pdf_text = ""

            if pdf_text.strip():
                pdf_data = {}
                for line in pdf_text.splitlines():
                    line = line.strip()
                    if ":" not in line:
                        continue
                    field, value = line.split(":", 1)
                    pdf_data[field.strip()] = value.strip()

                if pdf_data:
                    df = pd.DataFrame([pdf_data])
                    st.success("✅ CSV ready for download!")
                    st.dataframe(df)

                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_bytes,
                        file_name="direct_pdf_extraction.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ No data extracted from this PDF.")

    # -------------------- OCR Extraction to CSV (Table Format) --------------------
    with col2:
        if st.button("Table Extraction to CSV (OCR)"):
            uploaded_file.seek(0)
            extracted_data = []

            try:
                pdf_images = convert_from_bytes(uploaded_file.read())

                all_ocr_text = []  # For debugging
                for i, page_img in enumerate(pdf_images):
                    # OCR extract text from image
                    text = pytesseract.image_to_string(page_img)
                    all_ocr_text.append(f"--- Page {i+1} ---\n{text}")
                    lines = [l.strip() for l in text.splitlines() if l.strip()]

                    for line in lines:
                        # Try different splitting strategies
                        if "\t" in line:
                            columns = line.split("\t")
                        else:
                            columns = re.split(r"\s{2,}", line)

                        # Keep rows that look like a table (2+ columns)
                        if len(columns) > 1:
                            extracted_data.append([col.strip() for col in columns if col.strip()])

                if extracted_data:
                    # First row = headers, rest = data rows
                    headers = extracted_data[0]
                    rows = extracted_data[1:]

                    # Pad rows to match header length
                    max_len = len(headers)
                    rows = [
                        row + [""] * (max_len - len(row)) if len(row) < max_len else row[:max_len]
                        for row in rows
                    ]

                    df = pd.DataFrame(rows, columns=headers)
                    st.success("✅ Table data extracted with OCR!")
                    st.dataframe(df)

                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_bytes,
                        file_name="table_pdf_extraction.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ OCR text extracted, but no table-like structure was detected.")

                # Optional debug view
                if st.checkbox("🔍 Show raw OCR text"):
                    st.text("\n\n".join(all_ocr_text))

            except Exception as e:
                st.error(f"OCR extraction failed: {e}")
