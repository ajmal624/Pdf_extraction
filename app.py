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

if uploaded_file:
    # -------------------- PDF Preview --------------------
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

    # -------------------- Direct PDF Extraction --------------------
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

    # -------------------- OCR Table Extraction → Word → CSV --------------------
    with col2:
        if st.button("OCR Scanned PDF → Word → CSV"):
            uploaded_file.seek(0)
            try:
                pdf_images = convert_from_bytes(uploaded_file.read())
                word_doc = Document()
                word_doc.add_heading("Extracted OCR Data", level=1)
                extracted_records = []

                for page_num, page_img in enumerate(pdf_images, start=1):
                    # OCR text
                    text = pytesseract.image_to_string(page_img)
                    lines = [line.strip() for line in text.splitlines() if line.strip()]

                    if not lines:
                        continue

                    # heuristic: detect tables as consecutive non-empty lines
                    # assume each two consecutive lines = fields & values
                    for i in range(0, len(lines)-1, 2):
                        fields_line = lines[i].split()
                        values_line = lines[i+1].split()
                        record = {}
                        for f, v in zip(fields_line, values_line):
                            record[f] = v
                        if record:
                            extracted_records.append(record)
                            # add to Word table
                            table = word_doc.add_table(rows=1, cols=2)
                            hdr_cells = table.rows[0].cells
                            hdr_cells[0].text = "Field"
                            hdr_cells[1].text = "Value"
                            for field, value in record.items():
                                row_cells = table.add_row().cells
                                row_cells[0].text = field
                                row_cells[1].text = value
                            word_doc.add_paragraph()

                if extracted_records:
                    # Save Word
                    word_bytes = BytesIO()
                    word_doc.save(word_bytes)
                    word_bytes.seek(0)
                    st.download_button(
                        "📥 Download Word Document",
                        data=word_bytes,
                        file_name="ocr_extraction.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                    # Save CSV
                    df = pd.DataFrame(extracted_records)
                    st.dataframe(df)
                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_bytes,
                        file_name="ocr_extraction.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ OCR could not detect tables/fields in this PDF.")

            except Exception as e:
                st.error(f"OCR → Word → CSV extraction failed: {e}")
