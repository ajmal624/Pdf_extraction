import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pandas as pd
import pytesseract
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# -------------------- Helper: Preprocess --------------------
def preprocess_image(image: Image.Image) -> Image.Image:
    """Convert to grayscale for better OCR."""
    return image.convert("L")

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

    # -------------------- Direct Extraction --------------------
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

    # -------------------- OCR Table Extraction --------------------
    with col2:
        if st.button("OCR Table Extraction to CSV"):
            uploaded_file.seek(0)
            all_records = []

            try:
                pdf_images = convert_from_bytes(uploaded_file.read())
                debug_texts = []

                for page_idx, page_img in enumerate(pdf_images):
                    processed_img = preprocess_image(page_img)

                    # OCR with word-level bounding boxes
                    data = pytesseract.image_to_data(
                        processed_img,
                        output_type=pytesseract.Output.DATAFRAME,
                        config="--psm 6"
                    )

                    data = data.dropna(subset=["text"])
                    if data.empty:
                        continue

                    # Collect debug OCR text
                    debug_texts.append(f"--- Page {page_idx+1} ---\n" + "\n".join(data["text"].tolist()))

                    # Group words into rows
                    page_rows = []
                    for _, row_group in data.groupby("line_num"):
                        words = row_group[["left", "text"]].values.tolist()
                        words = [(int(x), str(t).strip()) for x, t in words if t.strip()]
                        if not words:
                            continue
                        words.sort(key=lambda x: x[0])  # left to right
                        row_text = [w for _, w in words]
                        page_rows.append(row_text)

                    # Each table = 3 rows (title, fields, values)
                    for idx in range(0, len(page_rows), 3):
                        if idx + 2 < len(page_rows):
                            fields = page_rows[idx + 1]
                            values = page_rows[idx + 2]

                            # Normalize lengths
                            max_len = max(len(fields), len(values))
                            fields = fields + [""] * (max_len - len(fields))
                            values = values + [""] * (max_len - len(values))

                            record = {
                                f.strip(): v.strip() if v else ""
                                for f, v in zip(fields, values) if f.strip()
                            }

                            if record:
                                record["Page"] = page_idx + 1
                                all_records.append(record)

                if all_records:
                    df = pd.DataFrame(all_records)
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
                    st.warning("⚠️ OCR text extracted, but no tables found.")

                if st.checkbox("🔍 Show raw OCR text"):
                    st.text("\n\n".join(debug_texts))

            except Exception as e:
                st.error(f"OCR extraction failed: {e}")
