import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.subheader("📖 PDF Preview")

    try:
        # Convert PDF pages to images
        pages = convert_from_bytes(uploaded_file.read())
        for i, page in enumerate(pages):
            st.image(page, caption=f"Page {i+1}", use_column_width=True)
    except Exception as e:
        st.error(f"Failed to render PDF: {e}")

    st.write("---")
    st.subheader("⚡ Extraction Options")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Direct PDF Extraction"):
            uploaded_file.seek(0)  # Reset pointer
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
                st.success("✅ Text extracted successfully!")
                st.text_area("Extracted Text", pdf_text, height=300)
            else:
                st.warning("⚠️ No text found. It might be scanned. Use table extraction instead.")

    with col2:
        if st.button("Table Extraction to CSV"):
            uploaded_file.seek(0)
            # OCR extraction page by page
            extracted_data = []
            for i, page_img in enumerate(convert_from_bytes(uploaded_file.read())):
                text = pytesseract.image_to_string(page_img)
                lines = text.splitlines()
                page_dict = {}
                current_field = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # If line looks like a field, store value
                    if len(line.split()) <= 5 and not any(c.isdigit() for c in line):
                        current_field = line
                        page_dict[current_field] = ""
                    elif current_field:
                        page_dict[current_field] += (" " + line if page_dict[current_field] else line)

                if page_dict:
                    extracted_data.append(page_dict)

            if extracted_data:
                df = pd.DataFrame(extracted_data)
                st.success("✅ Table data extracted!")
                st.dataframe(df)

                csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                st.download_button(
                    "📥 Download CSV",
                    data=csv_bytes,
                    file_name="extracted_table_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ No table data could be extracted from this PDF.")
