def extract_fields_advanced(text):
    text = clean_text(text)

    fields = [
        "How did you hear about us",
        "Date",
        "Client Information",
        "Name",
        "Telephone",
        "Email",
        "Property Address",
        "Address",
        "Property Location",
        "Property Information",
        "Commercial or Mixed",
        "Commercial isal?",
        "Address or Mixed",
        "Reason for appraisal",
        "Appraisal Information",
        "Appraiser Fee",
        "Appraiser",
        "Fee",
        "Scheduled date",
        "Scheduled time",
        "ETA",
        "Access",
        "Name on report"
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
        else:
            value = ""
        combined.append((field_name, value))
        i += 2

    result = {}

    def parse_client_info(text):
        name = ""
        telephone = ""
        email = ""

        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        if email_match:
            email = email_match.group(0)

        phone_match = re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
        if phone_match:
            telephone = phone_match.group(0)

        name = text
        if email:
            name = name.replace(email, "")
        if telephone:
            name = name.replace(telephone, "")
        name = name.strip(" |,-")

        return name.strip(), telephone.strip(), email.strip()

    # Temporary holders for merging
    property_info_text = ""
    address_or_mixed_text = ""
    appraiser_fee_text = ""

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
            date_match = re.search(r"\b\d{1,2}/\d{1,2}\b|\b\w{3}-\d{1,2}\b", value)
            time_match = re.search(r"\b\d{1,2}:\d{2}\s*(am|pm)?\b", value, re.I)
            if date_match:
                result["Scheduled date"] = date_match.group(0)
            if time_match:
                result["Scheduled time"] = time_match.group(0)
            else:
                result["Scheduled time"] = value.strip()
        elif field == "Property Information":
            property_info_text += " " + value
        elif field == "Address or Mixed":
            address_or_mixed_text += " " + value
        elif field in ["Appraiser Fee", "Appraiser", "Fee"]:
            appraiser_fee_text += " " + value
        else:
            cleaned_value = re.sub(rf"^{re.escape(field)}[:\-]?\s*", "", value, flags=re.I).strip()
            if cleaned_value:
                result[field] = cleaned_value

    # Merge and clean Property Address and Commercial info
    combined_property_text = (property_info_text + " " + address_or_mixed_text).strip()
    if combined_property_text:
        # Try to extract address from combined text
        address_match = re.search(r"\d+\s+[A-Za-z0-9\s.,\-]+", combined_property_text)
        if address_match:
            result["Property Address"] = address_match.group(0).strip()
        # Also keep combined property info
        result["Property Information"] = combined_property_text

    # Clean and assign Appraiser Fee
    if appraiser_fee_text.strip():
        result["Appraiser Fee"] = appraiser_fee_text.strip()

    return list(result.items())

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

        # Trim extra spaces
        value = value.strip()

        cleaned.append((field, value))
    return cleaned
