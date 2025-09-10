import streamlit as st
import pandas as pd
from docx import Document
import io

st.set_page_config(layout="wide")
st.title("DOCX → CSV Extractor (Bold=Value, Regular=Field)")

def extract_docx_bold_values(docx_file):
    """
    Extract fields and values from Word file based on bold formatting.
    Bold text is treated as value, regular as field.
    Returns dict {field: value}.
    """
    doc = Document(docx_file)
    fields = []
    values = []

    # Process paragraphs
    for para in doc.paragraphs:
        current_field = ""
        current_value = ""
        for run in para.runs:
            text = run.text.strip()
            if not text:
                continue
            if run.bold:
                # Bold → value
                current_value += (text + " ")
            else:
                # Regular → field
                current_field += (text + " ")

        # If we have both field and value, store them
        if current_field and current_value:
            fields.append(current_field.strip())
            values.append(current_value.strip())

    # Process tables
    for table in doc.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                cell_text = ""
                for para in cell.paragraphs:
                    for run in para.runs:
                        cell_text += run.text.strip() + " "
                cells.append(cell_text.strip())
            # Pair sequential cells: non-bold=field, bold=value
            i = 0
            while i + 1 < len(cells):
                fields.append(cells[i])
                values.append(cells[i + 1])
                i += 2

    # Merge into dict
    final_dict = {}
    for f, v in zip(fields, values):
        final_dict[f] = v

    return final_dict

# ---------- Streamlit UI ----------
uploaded_files = st.file_uploader(
    "Upload one or more DOCX files", type=["docx"], accept_multiple_files=True
)

if uploaded_files:
    all_rows = []
    all_fields = set()

    for uploaded in uploaded_files:
        try:
            row_dict = extract_docx_bold_values(uploaded)
            all_fields.update(row_dict.keys())
            all_rows.append(row_dict)
        except Exception as e:
            st.error(f"Error reading {uploaded.name}: {e}")

    if all_rows:
        # Sort fields for consistent column order
        all_fields = list(all_fields)

        final_data = []
        for row in all_rows:
            final_row = [row.get(f, "") for f in all_fields]
            final_data.append(final_row)

        final_df = pd.DataFrame(final_data, columns=all_fields)
        st.markdown("### Extracted Data")
        st.dataframe(final_df)

        # Download CSV
        buffer = io.StringIO()
        final_df.to_csv(buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=buffer.getvalue().encode("utf-8"),
            file_name="extracted_docx_data.csv",
            mime="text/csv"
        )
else:
    st.info("Upload one or more DOCX files to extract fields and values.")

st.markdown("""
**How this works:**  
- **Bold text** in Word is treated as value  
- **Regular text** is treated as field  
- Handles **paragraphs and tables**  
- Produces a CSV with:
  - Columns = fields
  - Rows = one DOCX per row
""")
