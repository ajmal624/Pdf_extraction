import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
from io import BytesIO
from docx import Document

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

    # -------------------- OCR/Table Extraction --------------------
    with col2:
        if st.button("Table Extraction to Word/CSV"):
            uploaded_file.seek(0)
            extracted_records = []
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    all_tables = []
                    # Collect all tables with page and table index
                    for page_num, page in enumerate(pdf.pages, start=1):
                        tables = page.extract_tables()
                        for tidx, table in enumerate(tables, start=1):
                            all_tables.append((page_num, tidx, table))

                if not all_tables:
                    st.warning("⚠️ No tables found in this PDF.")
                else:
                    st.success(f"✅ Found {len(all_tables)} tables!")

                    for page_num, tidx, table in all_tables:
                        st.write(f"### Table {tidx} (Page {page_num})")
                        df_preview = pd.DataFrame(table)
                        st.dataframe(df_preview)

                        # Let user select rows for fields and values
                        field_row = st.number_input(
                            f"Select field row for Table {tidx} (Page {page_num})",
                            min_value=0, max_value=len(table)-1, value=0, step=1, key=f"field_{page_num}_{tidx}"
                        )
                        value_row = st.number_input(
                            f"Select value row for Table {tidx} (Page {page_num})",
                            min_value=0, max_value=len(table)-1, value=1, step=1, key=f"value_{page_num}_{tidx}"
                        )

                        if st.button(f"Extract Table {tidx} (Page {page_num})", key=f"extract_{page_num}_{tidx}"):
                            fields = table[field_row]
                            values = table[value_row]
                            record = {}
                            for f, v in zip(fields, values):
                                if f and v:
                                    record[str(f).strip()] = str(v).strip()
                            if record:
                                extracted_records.append(record)
                                st.success(f"✅ Extracted {len(record)} fields from Table {tidx} (Page {page_num})")
                                st.json(record)

                # Download final results
                if extracted_records:
                    df = pd.DataFrame(extracted_records)
                    st.write("### Final Extracted Data")
                    st.dataframe(df)

                    # Save to Word
                    doc = Document()
                    doc.add_heading("Extracted Table Data", level=1)
                    for idx, record in enumerate(extracted_records, start=1):
                        doc.add_heading(f"Record {idx}", level=2)
                        table_doc = doc.add_table(rows=1, cols=2)
                        hdr_cells = table_doc.rows[0].cells
                        hdr_cells[0].text = "Field"
                        hdr_cells[1].text = "Value"
                        for field, value in record.items():
                            row_cells = table_doc.add_row().cells
                            row_cells[0].text = str(field)
                            row_cells[1].text = str(value)
                        doc.add_paragraph()

                    word_bytes = BytesIO()
                    doc.save(word_bytes)
                    word_bytes.seek(0)

                    st.download_button(
                        "📥 Download Word Document",
                        data=word_bytes,
                        file_name="ocr_extraction.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                    # CSV download
                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_bytes,
                        file_name="ocr_extraction.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"Table extraction failed: {e}")
