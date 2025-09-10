import streamlit as st
import pandas as pd
import pdfplumber
import io

st.set_page_config(layout="wide")
st.title("PDF → CSV Extractor (Bold=Value, Regular=Field)")

def extract_pdf_bold_values(pdf_file):
    """
    Extract fields and values from PDF.
    Bold text is treated as value, regular as field.
    Returns dict {field: value}.
    """
    fields = []
    values = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            words = page.extract_words(extra_attrs=["fontname", "size"])
            
            # Group consecutive bold or regular words
            i = 0
            while i < len(words):
                word = words[i]
                text = word["text"].strip()
                font = word["fontname"].lower()

                # Treat bold fonts as value
                if "bold" in font:
                    # Merge consecutive bold words
                    value_text = [text]
                    i += 1
                    while i < len(words) and "bold" in words[i]["fontname"].lower():
                        value_text.append(words[i]["text"].strip())
                        i += 1
                    values.append(" ".join(value_text))
                else:
                    # Merge consecutive regular words as field
                    field_text = [text]
                    i += 1
                    while i < len(words) and "bold" not in words[i]["fontname"].lower():
                        field_text.append(words[i]["text"].strip())
                        i += 1
                    fields.append(" ".join(field_text))

    # Pair fields and values
    final_dict = {}
    for f, v in zip(fields, values):
        final_dict[f] = v

    return final_dict

# ---------- Streamlit UI ----------
uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    all_rows = []
    all_fields = set()

    for uploaded in uploaded_files:
        try:
            row_dict = extract_pdf_bold_values(uploaded)
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
            file_name="extracted_pdf_data.csv",
            mime="text/csv"
        )
else:
    st.info("Upload one or more PDF files to extract fields and values.")

st.markdown("""
**How this works:**  
- **Bold text** is treated as the value  
- **Regular text** is treated as the field  
- Handles **multi-word fields and values**  
- Produces a CSV with:
  - Columns = fields
  - Rows = one PDF per row
""")
