import re
from datetime import datetime

def extract_and_clean_fields(text):
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

    property_info_text = ""
    address_or_mixed_text = ""
    commercial_or_mixed_text = ""
    reason_for_appraisal_text = ""
    appraiser_fee_text = ""
    eta_text = ""
    access_text = ""

    for field, value in combined:
        # Remove repeated label prefixes from values
        if field.lower() in ["reason for appraisal", "name on report", "scheduled date", "appraiser fee"]:
            # Remove field name + colon from start of value if present
            prefix_pattern = re.compile(rf"^{re.escape(field)}[:\-]?\s*", re.I)
            value = prefix_pattern.sub("", value).strip()

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
            time_match = re.search(r"\b\d{1,2}:\d{2}\s*(am|pm)?\b", value, re.I)
            if time_match:
                result["Scheduled time"] = time_match.group(0)
            else:
                result["Scheduled time"] = value.strip()
        elif field == "Scheduled date":
            try:
                dt = datetime.strptime(value, "%m/%d/%y")
                result["Scheduled date"] = dt.strftime("%b-%d")
            except Exception:
                result["Scheduled date"] = value.strip()
        elif field == "ETA":
            eta_text += " " + value
        elif field == "Access":
            access_text += " " + value
        elif field == "Property Information":
            property_info_text += " " + value
        elif field == "Address or Mixed":
            address_or_mixed_text += " " + value
        elif field == "Commercial or Mixed":
            commercial_or_mixed_text += " " + value
        elif field == "Reason for appraisal":
            reason_for_appraisal_text += " " + value
        elif field in ["Appraiser Fee", "Appraiser", "Fee"]:
            appraiser_fee_text += " " + value
        else:
            cleaned_value = re.sub(rf"^{re.escape(field)}[:\-]?\s*", "", value, flags=re.I).strip()
            if cleaned_value:
                result[field] = cleaned_value

    # Extract Property Address from Reason for appraisal text if missing
    if "Property Address" not in result and reason_for_appraisal_text:
        # Try to extract address pattern (number + street + city + state + zip)
        address_match = re.search(r"\d+\s+[A-Za-z0-9\s.,\-]+(?:NY|New York|NY\s)?\s*\d{5}", reason_for_appraisal_text)
        if not address_match:
            address_match = re.search(r"\d+\s+[A-Za-z0-9\s.,\-]+", reason_for_appraisal_text)
        if address_match:
            result["Property Address"] = address_match.group(0).strip()

    # Commercial or Mixed
    commercial_text = commercial_or_mixed_text.strip()
    if not commercial_text and "Commercial or Mixed" not in result:
        if "mixed" in property_info_text.lower():
            commercial_text = "Mixed"
    if commercial_text:
        result["Commercial or Mixed"] = commercial_text

    # Reason for appraisal
    if reason_for_appraisal_text:
        reason_clean = reason_for_appraisal_text.replace('“', '"').replace('”', '"').replace('–', '-').strip()
        result["Reason for appraisal"] = reason_clean

    # Appraiser Fee
    if appraiser_fee_text.strip():
        result["Appraiser Fee"] = appraiser_fee_text.strip()

    # ETA Standard
    if eta_text.strip():
        result["ETA Standard"] = eta_text.strip()

    # Access
    if access_text.strip():
        access_val = access_text.strip()
        if not access_val.lower().startswith("access to"):
            access_val = "Access to " + access_val
        result["Access"] = access_val

    # Clean Name on report
    if "Name on report" in result:
        result["Name on report"] = result["Name on report"].lstrip("on report:").strip()

    # Clean How did you hear about us
    if "How did you hear about us" in result:
        result["How did you hear about us"] = result["How did you hear about us"].lstrip("- ").strip()

    # Clean Client Name (remove stray "Email" word)
    if "Client Name" in result:
        result["Client Name"] = re.sub(r"\bEmail\b", "", result["Client Name"], flags=re.I).strip()

    return list(result.items())
