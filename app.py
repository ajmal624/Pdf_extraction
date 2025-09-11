import streamlit as st
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import re
from PIL import Image
 
# ---------------------------------------------------------
# Streamlit Page Config
# ---------------------------------------------------------
st.set_page_config(page_title="OCR to CSV Extractor", page_icon="📄")
 
st.title("📄 OCR to CSV Extractor")
st.write("Upload a scanned PDF or image. Extracts fields and exports to CSV.")
 
# ---------------------------------------------------------
# Helper Function
# ---------------------------------------------------------
def parse_fields(text: str) -> dict:
    fields = {
        "Date": "",
        "Name": "",
        "Telephone": "",
        "Email": "",
        "Address": "",
        "Type": "",
        "Reason for Appraisal": "",
        "Appraiser Fee": "",
        "Scheduled Date": "",
        "Scheduled Time": "",
    }
 
    # Date
    match = re.search(r"Date[:\s]*([\d/]+)", text, re.IGNORECASE)
    if match:
        fields["Date"] = match.group(1).strip()
 
    # Telephone
    match = re.search(r"(\d{3}[-\s]\d{3}[-\s]\d{4})", text)
    if match:
        fields["Telephone"] = match.group(1).strip()
 
    # Email
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if match:
        fields["Email"] = match.group(0).strip()
 
    # Name (line before Telephone)
    if fields["Telephone"]:
        tel_index = text.find(fields["Telephone"])
        before_tel = text[:tel_index].splitlines()
        for line in reversed(before_tel):
            if line.strip() and not any(x in line.lower() for x in ["client information", "name", "telephone", "email"]):
                fields["Name"] = line.strip()
                break
 
    # Address (capture up to Liberty, NY + ZIP)
    match = re.search(r"(\d+\s?[A-Za-z]+\s+.*Liberty,\s*NY\s*\d{5})", text, re.IGNORECASE)
    if match:
        addr = match.group(1).strip()
        zip_match = re.search(r"\d{5}", addr)
        if zip_match:
            addr = addr[: zip_match.end()]
        fields["Address"] = addr
 
    # Type
    match = re.search(r"(Commercial|Mixed)", text, re.IGNORECASE)
    if match:
        fields["Type"] = match.group(1).strip()
 
    # Reason for Appraisal
    match = re.search(r"Reason.*?\n(.*)", text, re.IGNORECASE | re.DOTALL)
    if match:
        fields["Reason for Appraisal"] = match.group(1).strip()
 
    # Appraiser Fee
    match = re.search(r"\$[0-9,]+.*", text)
    if match:
        fields["Appraiser Fee"] = match.group(0).strip()
 
    # Scheduled Date
    match = re.search(r"(\d{1,2}/\d{1,2}(?:/\d{2,4})?)", text)
    if match:
        date_val = match.group(1)
        if date_val != fields["Date"]:  # avoid duplicate with top date
            fields["Scheduled Date"] = date_val
 
    # Scheduled Time
    match = re.search(r"(\d{1,2}:\d{2}\s*(?:am|pm))", text, re.IGNORECASE)
    if match:
        fields["Scheduled Time"] = match.group(1).strip()
 
    return fields
 
# ---------------------------------------------------------
# File Uploader
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Upload PDF/Image", type=["pdf", "jpg", "jpeg", "png"])
 
if uploaded_file:
    text = ""
 
    if uploaded_file.type == "application/pdf":
        pages = convert_from_path(uploaded_file, dpi=300)
        for page in pages:
            text += pytesseract.image_to_string(page)
    else:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
 
    st.subheader("📑 Extracted Text (Raw)")
    st.text(text)
 
    fields = parse_fields(text)
    df = pd.DataFrame([fields])
 
    st.subheader("📊 Extracted Data (Structured)")
    st.dataframe(df)
 
    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "output.csv", "text/csv")
