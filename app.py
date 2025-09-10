def extract_fields_advanced(text):
    text = clean_text(text)

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
        "Scheduled date",
        "Scheduled time",
        "ETA",
        "Access",
        "Name on report",
        # Add these explicitly if your OCR text uses these exact headers
        "Address",
        "Appraiser",
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
            # For multiline fields like Address or Appraiser, try to accumulate more text
            # until next known field or end of text
            j = i + 2
            while j < len(parts) and not any(parts[j].strip().startswith(f) for f in fields):
                value += " " + parts[j].strip()
                j += 1
            i = j - 1
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
        else:
            cleaned_value = re.sub(rf"^{re.escape(field)}[:\-]?\s*", "", value, flags=re.I).strip()
            if cleaned_value:
                result[field] = cleaned_value

    return list(result.items())
