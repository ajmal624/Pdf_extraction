import streamlit as st
import pdfplumber
import pandas as pd
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="📄 PDF Extractor", layout="wide")
st.title("📄 PDF Extraction App")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.subheader("📂 Uploaded File")
    st.write(f"**Filename:** {uploaded_file.name}")

    # ✅ Preview PDF safely using components
    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%"
        height="600"
        style="border:none;"
    ></iframe>
    """
    components.html(pdf_display, height=600, scrolling=True)

    # --- Button 1: Extract Key:Value fields ---
    if st.button("🔎 Extract Text Fields"):
        pdf_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"

        pdf_data = {}
        for line in pdf_text.splitlines():
            line = line.strip()
            if not line:
                continue

            if "Due Date:" in line and "File ID" in line:
                parts = line.split("Due Date:")
                pdf_data["File ID"] = parts[0].replace("File ID", "").strip()
                pdf_data["Due Date"] = parts[1].strip()
                continue

            if ":" in line:
                field, value = line.split(":", 1)
                pdf_data[field.strip()] = value.strip()

        pdf_data["Filename"] = uploaded_file.name

        df = pd.DataFrame([pdf_data])
        st.subheader("✅ Extracted Fields")
        st.dataframe(df)

        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Download Extracted Fields (CSV)",
            data=csv,
            file_name="extracted_fields.csv",
            mime="text/csv"
        )

    # --- Button 2: Extract Tables ---
    if st.button("📊 Extract Tables"):
        all_tables = []
        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                for table in tables:
                    df_table = pd.DataFrame(table)
                    df_table["Page"] = i
                    all_tables.append(df_table)

        if all_tables:
            df_all = pd.concat(all_tables, ignore_index=True)
            st.subheader("📊 Extracted Tables")
            st.dataframe(df_all)

            csv = df_all.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Download Extracted Tables (CSV)",
                data=csv,
                file_name="extracted_tables.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ No tables detected in this PDF.")
