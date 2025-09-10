import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import StringIO

# OCR extraction from PDF bytes
def ocr_pdf(file_bytes):
    images = convert_from_bytes(file_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text

# Clean common OCR artifacts
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

# Extract fields and values by splitting text on known field names
def extract_fields_advanced(text):
    text = clean_text(text)

    # List of known fields (added Address and Appraiser)
    fields = [
        "How did you hear about us",
        "Date",
        "Client Information",
        "Name",
        "Telephone",
        "Email",
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

    escaped_fields = [re.escape(f) for f in fields]
    pattern = r"(?=(" + "|".join(escaped_fields) + r"))"
    parts = re.split(pattern, text)

    combined = []
    i = 1
    while i < len(parts):
        field_name = parts[i].strip()
        if i + 1 < len(parts):
            value = parts[i + 1].strip()

            # Accumulate multiline values for Address and Appraiser fields
            j = i + 2
            while j < len(parts) and not any(parts[j].strip().startswith(f) for f in fields):
                value += " " + parts[j].strip()
                j += 1
            i = j - 1
        else:
            value = ""
        combined.append((field_name, value))
        i += 2

    # Post-processing to merge and clean fields
    result = {}

    # Helper to extract subfields from Client Information block
    def parse_client_info(text):
        name = ""
        telephone = ""
        email = ""

        # Extract email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        if email_match:
            email = email_match.group(0)

        # Extract phone (basic pattern)
        phone_match = re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
        if phone_match:
            telephone = phone_match.group(0)

        # Remove email and phone from text to get name
        name = text
        if email:
            name = name.replace(email, "")
        if telephone:
            name = name.replace(telephone, "")
        name = name.strip(" |,-")

        return name.strip(), telephone.strip(), email.strip()

    for field, value in combined:
        if field == "Client Information":
            name, telephone, email = parse_client_info(value)
            if name:
                result["Client Name"] = name
            if telephone:
                result["Client Telephone"] = telephone
            if email:
                result["Client Email"] = email
        elif field == "Email":
            name, telephone, email = parse_client_info(value)
            if name:
                result["Client Name"] = name
            if telephone:
                result["Client Telephone"] = telephone
            if email:
                result["Client Email"] = email
        elif field == "Scheduled time":
            # Extract date and time if present in value
            date_match = re.search(r"\b\d{1,2}/\d{1,2}\b|\b\w{3}-\d{1,2}\b", value)
            time_match = re.search(r"\b\d{1,2}:\d{2}\s*(am|pm)?\b", value, re.I)
            if date_match:
                result["Scheduled date"] = date_match.group(0)
            if time_match:
                result["Scheduled time"] = time_match.group(0)
            else:
                result["Scheduled time"] = value.strip()
        else:
            # Remove repeated field name from value if present
            cleaned_value = re.sub(rf"^{re.escape(field)}[:\-]?\s*", "", value, flags=re.I).strip()
            if cleaned_value:
                result[field] = cleaned_value

    # If Address missing or empty, try to extract from Reason for appraisal or Property Information
    if "Address" not in result or not result["Address"]:
        for key in ["Reason for appraisal", "Property Information", "Address or Mixed"]:
            if key in result:
                # Simple regex for US address pattern (adjust if needed)
                addr_match = re.search(
                    r'(\d{1,5}\s[\w\s\.,\-]+,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5}(-\d{4})?)',
                    result[key]
                )
                if addr_match:
                    result["Address"] = addr_match.group(1).strip()
                    break

    # If Appraiser Fee missing, try to extract from Appraisal Information
    if ("Appraiser Fee" not in result or not result["Appraiser Fee"]) and "Appraisal Information" in result:
        fee_match = re.search(r"\$\d+(?:,\d{3})*(?:\.\d{2})?", result["Appraisal Information"])
        if fee_match:
            result["Appraiser Fee"] = fee_match.group(0)

    return list(result.items())

# Additional cleaning for slight fixes requested
def clean_extracted_data(extracted):
    cleaned = []
    for field, value in extracted:
        if field == "How did you hear about us":
            value = value.lstrip("- ").strip()

        if field == "Client Name":
            value = re.sub(r"\bEmail\b", "", value, flags=re.I).strip()

        if field == "Access":
            value = re.sub(r"^to\s+", "", value, flags=re.I).strip()

        if field == "Name":
            field = "Name on report"
            value = value.lstrip("on report:").strip()

        cleaned.append((field, value))
    return cleaned

def main():
    st.title("OCR PDF Field Extractor with Post-Processing")

    st.write("Upload an OCR-based PDF file. The app will perform OCR, extract fields (including Address and Appraiser), clean and parse them, then allow CSV download.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        with st.spinner("Performing OCR on PDF pages..."):
            text = ocr_pdf(file_bytes)

        if not text.strip():
            st.error("No text found after OCR. Please check the PDF or try a different file.")
            return

        extracted = extract_fields_advanced(text)
        extracted_cleaned = clean_extracted_data(extracted)

        if not extracted_cleaned:
            st.warning("No fields and values found with the current extraction pattern.")
            return

        df = pd.DataFrame(extracted_cleaned, columns=["Field", "Value"])

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
