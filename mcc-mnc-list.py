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


def filter(filters=None):
    """Filters records based on provided criteria."""
    if filters is None:
        return records

    if not isinstance(filters, dict):
        raise TypeError("Invalid parameter (dict expected)")

    status_code = None
    mcc = None
    mnc = None
    country_code = None

    if "statusCode" in filters:
        status_code = filters["statusCode"]
        if status_code not in status_codes_list():
            raise TypeError("Invalid statusCode parameter (not found in statusCode list)")

    if "mccmnc" in filters:
        if isinstance(filters["mccmnc"], (str, int)):
            mccmnc = str(filters["mccmnc"])
            mcc, mnc = mccmnc[:3], mccmnc[3:]
        else:
            raise TypeError("Invalid mccmnc parameter (string expected)")

    if "mcc" in filters and mcc is not None:
        raise TypeError("Don't use mccmnc and mcc parameter at once")
    if "mnc" in filters and mnc is not None:
        raise TypeError("Don't use mccmnc and mnc parameter at once")

    if "mcc" in filters:
        if isinstance(filters["mcc"], (str, int)):
            mcc = str(filters["mcc"])
        else:
            raise TypeError("Invalid mcc parameter (string expected)")

    if "mnc" in filters:
        if isinstance(filters["mnc"], (str, int)):
            mnc = str(filters["mnc"])
        else:
            raise TypeError("Invalid mnc parameter (string expected)")

    if "countryCode" in filters:
        if isinstance(filters["countryCode"], str):
            country_code = filters["countryCode"]
        else:
            raise TypeError("Invalid countryCode parameter (string expected)")

    result = records

    if status_code:
        result = [record for record in result if record.get("status") == status_code]
    if country_code:
        result = [record for record in result if record.get("countryCode") == country_code]
    if mcc:
        result = [record for record in result if record.get("mcc") == mcc]
    if mnc:
        result = [record for record in result if record.get("mnc") == mnc]

    return result


def find(filters):
    """Returns the first matching record or None."""
    return next(iter(filter(filters)), None)
