import streamlit as st
import pandas as pd
from docx import Document
import io
import re

def extract_docx_smart(file):
    doc = Document(file)
    data = []

    # First, try to extract tables (forms are often in tables)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) >= 2:
                field = cells[0]
                value = cells[1]
                data.append((field, value))

    # Next, parse free text paragraphs
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for para in paragraphs:
        if ":" in para:
            field, value = para.split(":", 1)
            data.append((field.strip(), value.strip()))
        else:
            # Add non-labeled lines as their own row
            data.append(("Unlabeled", para))

    # Clean duplicates
    seen = set()
    cleaned_data = []
    for field, value in data:
        if (field, value) not in seen and value:
            cleaned_data.append((field, value))
            seen.add((field, value))

    df = pd.DataFrame(cleaned_data, columns=["Field", "Value"])
    return df

# ---------- Streamlit App ----------
st.title("Smart DOCX to CSV Extractor")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])

if uploaded_file:
    df = extract_docx_smart(uploaded_file)
    st.subheader("Extracted Data")
    st.dataframe(df)

    # Convert DataFrame to CSV
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    st.download_button(
        label="Download CSV",
        data=csv_buffer,
        file_name="extracted_data.csv",
        mime="text/csv"
    )
