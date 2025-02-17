import json
import status_codes  # Importing the status_codes.py module

# Load JSON data from files
with open('./mcc-mnc-list.json', 'r') as file:
    records = json.load(file)


def all():
    """Returns all records."""
    return records


def status_codes_list():
    """Returns the list of status codes."""
    return status_codes.status_code_list  # Assuming status_codes.py defines `status_code_list`


def validate_string(value, name):
    """Helper function to ensure value is a string."""
    if not isinstance(value, (str, int)):
        raise ValueError(f"Invalid {name} parameter (string expected)")
    return str(value)


def filter(filters=None):
    """Filters records based on provided criteria."""
    if filters is None:
        return records

    if not isinstance(filters, dict):
        raise TypeError("Invalid parameter: filters must be a dictionary")

    status_code = filters.get("statusCode")
    country_code = filters.get("countryCode")
    mcc, mnc = None, None

    if "statusCode" in filters:
        if status_code not in status_codes_list():
            raise ValueError(f"Invalid statusCode: {status_code} not found in status codes list")

    if "mccmnc" in filters:
        mccmnc = validate_string(filters["mccmnc"], "mccmnc")
        mcc, mnc = mccmnc[:3], mccmnc[3:]

    if "mcc" in filters:
        if mcc is not None:
            raise ValueError("Don't use both mccmnc and mcc parameters")
        mcc = validate_string(filters["mcc"], "mcc")

    if "mnc" in filters:
        if mnc is not None:
            raise ValueError("Don't use both mccmnc and mnc parameters")
        mnc = validate_string(filters["mnc"], "mnc")

    if "countryCode" in filters:
        country_code = validate_string(filters["countryCode"], "countryCode")

    # Apply filtering
    return [
        record for record in records
        if (not status_code or record.get("status") == status_code) and
           (not country_code or record.get("countryCode") == country_code) and
           (not mcc or record.get("mcc") == mcc) and
           (not mnc or record.get("mnc") == mnc)
    ]


def find(filters):
    """Returns the first matching record or None."""
    return next(iter(filter(filters)), None)
