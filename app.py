import streamlit as st
import pdfplumber
import pandas as pd
from pdf2image import convert_from_bytes

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor App")

# --- Upload PDF ---
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.subheader("📂 PDF Preview")
    # Preview PDF as images
    try:
        images = convert_from_bytes(uploaded_file.getvalue())
        for i, img in enumerate(images):
            st.image(img, caption=f"Page {i+1}", use_column_width=True)
    except Exception as e:
        st.error(f"❌ Unable to render PDF preview: {e}")

    # --- Buttons ---
    col1, col2 = st.columns(2)

    # ----------- Button 1: Extract Fields -----------
    with col1:
        if st.button("📝 Extract Fields"):
            pdf_text = ""
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pdf_text += text + "\n"
            except Exception as e:
                st.error(f"❌ Failed to read PDF text: {e}")
                pdf_text = ""

            if pdf_text.strip() == "":
                st.warning("⚠️ No text found in this PDF. It might be scanned or image-based.")
            else:
                pdf_data = {}
                for line in pdf_text.splitlines():
                    line = line.strip()
                    if ":" not in line:
                        continue  # skip lines without ":"
                    field, value = line.split(":", 1)
                    field = field.strip()
                    value = value.strip()
                    if field and value:
                        pdf_data[field] = value
                pdf_data["Filename"] = uploaded_file.name

                df = pd.DataFrame([pdf_data])
                st.subheader("✅ Extracted Fields")
                st.dataframe(df)

    # ----------- Button 2: Extract Table Data -----------
    with col2:
        if st.button("📊 Extract Table to CSV"):
            pdf_text = ""
            try:
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pdf_text += text + "\n"
            except Exception as e:
                st.error(f"❌ Failed to read PDF text: {e}")
                pdf_text = ""

            if pdf_text.strip() == "":
                st.warning("⚠️ No text found in this PDF. It might be scanned or image-based.")
            else:
                all_data = []
                pdf_data = {}
                for line in pdf_text.splitlines():
                    line = line.strip()
                    if ":" not in line:
                        continue
                    field, value = line.split(":", 1)
                    field = field.strip()
                    value = value.strip()
                    if field:
                        pdf_data[field] = value
                pdf_data["Filename"] = uploaded_file.name
                all_data.append(pdf_data)

                df_table = pd.DataFrame(all_data)
                st.subheader("✅ Table Extracted")
                st.dataframe(df_table)

                csv = df_table.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="extracted_table.csv",
                    mime="text/csv"
                )
