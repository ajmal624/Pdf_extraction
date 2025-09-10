import streamlit as st
import pandas as pd
from docx import Document
import io

def extract_docx_as_columns(file):
    doc = Document(file)
    data = {}

    # Extract data from tables
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) >= 2:
                field = cells[0].strip()
                value = cells[1].strip()
                if field and value:
                    data[field] = value

    # Extract data from paragraphs
    for para in doc.paragraphs:
        line = para.text.strip()
        if ":" in line:
            parts = line.split(":", 1)
            field, value = parts[0].strip(), parts[1].strip()
            if field and value:
                data[field] = value

    # Convert to DataFrame with one row
    df = pd.DataFrame([data])
    return df

# ---------- Streamlit App ----------
st.title("DOCX to CSV (Fields as Columns)")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])

if uploaded_file:
    df = extract_docx_as_columns(uploaded_file)
    st.subheader("Extracted Data (Fields as Columns)")
    st.dataframe(df)

    # Save as CSV
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    st.download_button(
        label="Download CSV",
        data=csv_buffer,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
