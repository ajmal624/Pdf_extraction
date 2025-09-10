import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO
import re
import numpy as np
from PIL import Image

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

# ----------- Preprocessing for better OCR (Pillow only) -----------
def preprocess_image(pil_img):
    img = pil_img.convert("L")  # grayscale
    img = img.point(lambda x: 0 if x < 150 else 255, "1")  # threshold
    return img

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
                current_field = None

                for line in pdf_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue

                    if ":" in line:  # Field: Value
                        field, value = line.split(":", 1)
                        pdf_data[field.strip()] = value.strip()
                        current_field = field.strip()
                    elif current_field:  # continuation of previous value
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

    # -------------------- OCR Extraction to CSV (Better Table Alignment) --------------------
    with col2:
        if st.button("Table Extraction to CSV (OCR)"):
            uploaded_file.seek(0)
            extracted_rows = []

            try:
                pdf_images = convert_from_bytes(uploaded_file.read())
                all_ocr_text = []

                for i, page_img in enumerate(pdf_images):
                    processed_img = preprocess_image(page_img)

                    # Get OCR results with positions
                    data = pytesseract.image_to_data(
                        processed_img,
                        output_type=pytesseract.Output.DATAFRAME,
                        config="--psm 6"
                    )

                    # Drop empty
                    data = data.dropna(subset=["text"])
                    if data.empty:
                        continue

                    all_ocr_text.append(f"--- Page {i+1} ---\n" + "\n".join(data["text"].tolist()))

                    # Group words by line_num
                    for line_num, row_group in data.groupby("line_num"):
                        words = row_group[["left", "text"]].values.tolist()
                        words = [(int(x), str(t).strip()) for x, t in words if t.strip()]

                        if not words:
                            continue

                        # Sort by x-position
                        words.sort(key=lambda x: x[0])

                        # Group into columns by x gaps
                        row = []
                        current_col = []
                        prev_x = None

                        for x, word in words:
                            if prev_x is not None and x - prev_x > 50:  # gap = new column
                                row.append(" ".join(current_col))
                                current_col = []
                            current_col.append(word)
                            prev_x = x
                        if current_col:
                            row.append(" ".join(current_col))

                        if len(row) > 1:  # keep tabular rows
                            extracted_rows.append(row)

                if extracted_rows:
                    headers = extracted_rows[0]
                    rows = extracted_rows[1:]

                    # Normalize row lengths
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

                if st.checkbox("🔍 Show raw OCR text"):
                    st.text("\n\n".join(all_ocr_text))

            except Exception as e:
                st.error(f"OCR extraction failed: {e}")
