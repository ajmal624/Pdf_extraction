import streamlit as st
import pandas as pd
from docx import Document
import io

# ---------- Helper Function ----------
def extract_docx_to_df(file):
    doc = Document(file)
    text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # Simple heuristic: split by ":" to make field-value pairs
    fields, values = [], []
    for line in text:
        if ":" in line:
            parts = line.split(":", 1)
            fields.append(parts[0].strip())
            values.append(parts[1].strip())
        else:
            # If no ":", treat entire line as value without a field
            fields.append("Unlabeled Field")
            values.append(line.strip())

    df = pd.DataFrame({"Field": fields, "Value": values})
    return df

# ---------- Streamlit UI ----------
st.title("DOCX to CSV Extractor")

uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])

if uploaded_file:
    df = extract_docx_to_df(uploaded_file)

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
