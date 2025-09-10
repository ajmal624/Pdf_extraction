import streamlit as st
import pandas as pd
from docx import Document
import io

def extract_docx_smart(file):
    doc = Document(file)
    data = []

    # Extract data from tables
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) >= 2:
                field = cells[0].strip()
                value = cells[1].strip()
                if field and value:  # Ignore empty fields
                    data.append((field, value))

    # Extract data from paragraphs
    for para in doc.paragraphs:
        line = para.text.strip()
        if ":" in line:
            parts = line.split(":", 1)
            field, value = parts[0].strip(), parts[1].strip()
            if field and value:
                data.append((field, value))

    # Create DataFrame
    df = pd.DataFrame(data, columns=["Field", "Value"])

    # Remove rows with 'Unlabeled' or empty fields
    df = df[~df["Field"].str.contains("Unlabeled", case=False, na=False)]
    df = df[df["Field"].str.strip() != ""]

    # Pivot to make fields as columns
    df = df.set_index("Field").T.reset_index(drop=True)
    return df

# ---------- Streamlit App ----------
st.title("Clean DOCX to CSV Extractor")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])

if uploaded_file:
    df = extract_docx_smart(uploaded_file)
    st.subheader("Extracted Data (One Row per Document)")
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
