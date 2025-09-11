import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
import io

# Clean the OCR text to remove unwanted characters and normalize spaces
def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+',' ', text)  # Remove non-ASCII chars
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    return text.strip()

# Dynamically extract field-value pairs from the cleaned text
def extract_fields(text):
    lines = text.splitlines()
    pairs = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Try to split by common separators
        if ':' in line:
            parts = line.split(':', 1)
            field = parts[0].strip()
            value = parts[1].strip()
            pairs.append((field, value))
        elif '|' in line:
            parts = line.split('|', 1)
            field = parts[0].strip()
            value = parts[1].strip()
            pairs.append((field, value))
        else:
            # Heuristic: treat line as field if it looks like a question or label
            if re.search(r'(Name|Email|Date|Address|Reason|Fee|Scheduled|report)', line, re.IGNORECASE):
                pairs.append((line, ""))
            else:
                # If previous line exists, append as value
                if pairs:
                    prev_field, prev_value = pairs[-1]
                    # Append this line to the previous value
                    new_value = prev_value + " " + line if prev_value else line
                    pairs[-1] = (prev_field, new_value.strip())
                else:
                    pairs.append((line, ""))
    return pairs

# Streamlit interface
st.title("Dynamic OCR Field Extractor")

uploaded_file = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    with st.spinner("Extracting and cleaning text..."):
        raw_text = pytesseract.image_to_string(image)
        cleaned = clean_text(raw_text)
        extracted = extract_fields(cleaned)
    
    st.subheader("Extracted Fields")
    df = pd.DataFrame(extracted, columns=["Field", "Value"])
    st.dataframe(df)

    # Convert to CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="extracted_fields.csv",
        mime="text/csv"
    )
