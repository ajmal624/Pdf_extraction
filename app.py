import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO
import re
from PIL import Image

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

# ----------- Preprocessing for better OCR -----------
def preprocess_image(pil_img):
    img = pil_img.convert("L")  # grayscale
    img = img.point(lambda x: 0 if x < 150 else 255, "1")  # binary threshold
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

    # -------------------- OCR Extraction to CSV (Fields=Row2, Values=Row3) --------------------
    with col2:
        if st.button("Table Extraction to CSV (OCR)"):
            uploaded_file.seek(0)
            all_records = []

            try:
                pdf_images = convert_from_bytes(uploaded_file.read())
                debug_texts = []

                for i, page_img in enumerate(pdf_images):
                    processed_img = preprocess_image(page_img)

                    # OCR with positions
                    data = pytesseract.image_to_data(
                        processed_img,
                        output_type=pytesseract.Output.DATAFRAME,
                        config="--psm 6"
                    )

                    data = data.dropna(subset=["text"])
                    if data.empty:
                        continue

                    debug_texts.append(f"--- Page {i+1} ---\n" + "\n".join(data["text"].tolist()))

                    # Group by line_num (rows)
                    page_rows = []
                    for line_num, row_group in data.groupby("line_num"):
                        words = row_group[["left", "text"]].values.tolist()
                        words = [(int(x), str(t).strip()) for x, t in words if t.strip()]
                        if not words:
                            continue
                        words.sort(key=lambda x: x[0])  # sort by x position
                        row_text = [w for _, w in words]
                        page_rows.append(row_text)

                    # Apply your rule: 2nd row = fields, 3rd row = values
                    if len(page_rows) >= 3:
                        fields = page_rows[1]
                        values = page_rows[2]

                        # Pad shorter list
                        max_len = max(len(fields), len(values))
                        fields += [""] * (max_len - len(fields))
                        values += [""] * (max_len - len(values))

                        record = dict(zip(fields, values))
                        all_records.append(record)

                if all_records:
                    df = pd.DataFrame(all_records)
                    st.success("✅ Field-Value pairs extracted with OCR!")
                    st.dataframe(df)

                    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_bytes,
                        file_name="ocr_field_value_extraction.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ OCR text extracted, but no valid table rows found.")

                if st.checkbox("🔍 Show raw OCR text"):
                    st.text("\n\n".join(debug_texts))

            except Exception as e:
                st.error(f"OCR extraction failed: {e}")
