import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import StringIO

def ocr_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

def clean_text(text):
    replacements = {
        "â€™": "'",
        "—": "-",
        "“": '"',
        "”": '"',
        "|": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def split_line_to_pairs(line):
    parts = re.split(r'\t+|\s{2,}', line.strip())
    pairs = []
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if ':' in part:
            field, value = part.split(':', 1)
            pairs.append((field.strip(), value.strip()))
            i += 1
        else:
            if i + 1 < len(parts):
                pairs.append((part, parts[i+1].strip()))
                i += 2
            else:
                pairs.append((part, ""))
                i += 1
    return pairs

def extract_address(text):
    address_pattern = re.compile(
        r'(\d{1,5}\s[\w\s\.,\-]+,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5}(-\d{4})?)',
        re.IGNORECASE
    )
    match = address_pattern.search(text)
    if match:
        return match.group(1).strip()
    return ""

def extract_fields_dynamic(text):
    text = clean_text(text)
    lines = text.splitlines()

    known_fields = [
        "How did you hear about us",
        "Date",
        "Client Name",
        "Client Telephone",
        "Client Email",
        "Property Information",
        "Commercial or Mixed",
        "Commercial isal?",
        "Address or Mixed",
        "Reason for appraisal",
        "Appraisal Information",
        "Appraiser Fee",
        "Appraiser",
        "Scheduled date",
        "Scheduled time",
        "ETA",
        "Access",
        "Name on report",
        "Address",
    ]

    known_fields_lower = [f.lower() for f in known_fields]

    extracted = []
    current_field = None
    current_value = []

    def save_current():
        if current_field:
            val = " ".join(current_value).strip()
            if val:
                extracted.append((current_field, val))

    for line in lines:
        pairs = split_line_to_pairs(line)
        if not pairs:
            if current_field:
                current_value.append(line.strip())
            continue

        for field, value in pairs:
            field_norm = field.lower()
            matched_field = None
            for kf in known_fields_lower:
                if kf in field_norm:
                    matched_field = known_fields[known_fields_lower.index(kf)]
                    break

            if matched_field:
                save_current()
                current_field = matched_field
                current_value = [value]
            else:
                if current_field:
                    current_value.append(field + " " + value)
                else:
                    extracted.append((field, value))

    save_current()

    result = {k: v for k, v in extracted}

    if "Address" not in result or not result["Address"]:
        for key in ["Reason for appraisal", "Property Information", "Address or Mixed"]:
            if key in result:
                addr = extract_address(result[key])
                if addr:
                    result["Address"] = addr
                    break

    if ("Appraiser" not in result or not result["Appraiser"]) and "Appraisal Information" in result:
        fee_match = re.search(r"\$\d+(?:,\d{3})*(?:\.\d{2})?", result["Appraisal Information"])
        if fee_match:
            result["Appraiser Fee"] = fee_match.group(0)

    return list(result.items())

def main():
    st.title("OCR PDF Field Extractor with Address and Appraiser Extraction")

    st.write("Upload an OCR-based PDF file. The app will extract fields including Address and Appraiser info.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted = extract_fields_dynamic(text)

        if not extracted:
            st.warning("No fields and values found.")
            return

        df = pd.DataFrame(extracted, columns=["Field", "Value"])

        st.subheader("Extracted Fields and Values")
        st.dataframe(df)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download extracted data as CSV",
            data=csv_data,
            file_name="extracted_fields.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
