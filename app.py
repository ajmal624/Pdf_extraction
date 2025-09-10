import streamlit as st
import pandas as pd
from docx import Document
import io
import re

def clean_field_name(field):
    # Normalize field names
    field = re.sub(r'\s+', ' ', field.strip())  # Remove extra spaces
    field = field.replace("\n", " ")
    return field

def extract_docx_clean_one_row(file):
    doc = Document(file)
    data = {}
    skip_headers = ["Client Information", "Property Information", "Appraisal Information"]

    # Extract tables
    for table in doc.tables:
        for row in table.rows:
            cells = [clean_field_name(c.text) for c in row.cells]
            if len(cells) >= 2:
                field, value = cells[0], cells[1]
                if field and value and field not in skip_headers:
                    data[field] = value

    # Extract paragraph data
    for para in doc.paragraphs:
        line = para.text.strip()
        if ":" in line:
            parts = line.split(":", 1)
            field, value = clean_field_name(parts[0]), clean_field_name(parts[1])
            if field and value and field not in skip_headers:
                data[field] = value

    # Create single-row DataFrame
    df = pd.DataFrame([data])
    return df

# ---------- Streamlit App ----------
st.title("DOCX to CSV (Clean Single-Row Extractor)")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])

if uploaded_file:
    df = extract_docx_clean_one_row(uploaded_file)
    st.subheader("Extracted Clean Table")
    st.dataframe(df)

    # Save CSV
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    st.download_button(
        label="Download CSV",
        data=csv_buffer,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
