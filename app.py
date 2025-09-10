import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO
from docx import Document
from PIL import Image

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])


# -------------------- Direct PDF Extraction --------------------
def direct_extraction(uploaded_file):
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
        return None

    if not pdf_text.strip():
        return None

    pdf_data = {}
    current_field = None
    for line in pdf_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if ":" in line:  # Field: Value
            field, value = line.split(":", 1)
            pdf_data[field.strip()] = value.strip()
            current_field = field.strip()
        elif current_field:  # continuation of previous field
            pdf_data[current_field] += " " + line

    return pdf_data if pdf_data else None


# -------------------- OCR Extraction (Tables only) --------------------
def ocr_extract_tables(uploaded_file):
    uploaded_file.seek(0)
    extracted_records = []

    try:
        # Convert each PDF page into an image
        pdf_images = convert_from_bytes(uploaded_file.read())

        # Create a temporary Word doc
        doc = Document()
        for page_num, page_img in enumerate(pdf_images, start=1):
            text = pytesseract.image_to_string(page_img)
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not lines:
                continue

            # Build a table in the Word doc (simulate table detection)
            table = doc.add_table(rows=0, cols=2)
            for line in lines:
                if ":" in line:  # Only take field:value style
                    field, value = line.split(":", 1)
                    row_cells = table.add_row().cells
                    row_cells[0].text = field.strip()
                    row_cells[1].text = value.strip()

        # Now parse the Word doc back for field:value pairs
        for table in doc.tables:
            record = {}
            for row in table.rows:
                if len(row.cells) >= 2:
                    field = row.cells[0].text.strip()
                    value = row.cells[1].text.strip()
                    if field and value:
                        record[field] = value
            if record:
                extracted_records.append(record)

        return extracted_records

    except Exception as e:
        st.error(f"OCR extraction failed: {e}")
        return []


# -------------------- Main App --------------------
if uploaded_file:
    st.subheader("📖 PDF Preview")
    try:
        pages = convert_from_bytes(uploaded_file.read())
        for i, page in enumerate(pages):
            st.image(page, caption=f"Page {i+1}", use_column_width=True)
    except Exception as e:
        st.error(f"Failed to render PDF: {e}")

    st.write("---")
    st.subheader("⚡ Extraction Options")

    col1, col2 = st.columns(2)

    # Direct Extraction
    with col1:
        if st.button("Direct PDF Extraction to CSV"):
            data = direct_extraction(uploaded_file)
            if data:
                df = pd.DataFrame([data])
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

    # OCR Extraction (Tables only → CSV)
    with col2:
        if st.button("OCR Table Extraction to CSV"):
            records = ocr_extract_tables(uploaded_file)

            if records:
                df = pd.DataFrame(records)
                st.success("✅ Field-Value pairs extracted from OCR tables!")
                st.dataframe(df)

                csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                st.download_button(
                    "📥 Download CSV",
                    data=csv_bytes,
                    file_name="ocr_table_extraction.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No valid tables found in OCR output.")
