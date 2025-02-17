import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/Mobile_country_code"
WIKI_URL_REGIONS = [
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_2xx_(Europe)",
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_3xx_(North_America)",
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_4xx_(Asia)",
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_5xx_(Oceania)",
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_6xx_(Africa)",
    "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_7xx_(South_America)"
]

MCC_MNC_OUTPUT_FILE = os.path.join(os.getcwd(), "mcc-mnc-list.json")
STATUS_CODES_OUTPUT_FILE = os.path.join(os.getcwd(), "status-codes.json")

# Initialize a session for better performance
session = requests.Session()

def fetch():
    """Fetches MCC-MNC data from Wikipedia and writes it to JSON files."""
    records = []
    status_codes = set()  # Use a set to avoid duplicates

    for region in WIKI_URL_REGIONS:
        collect(region, records, status_codes)
        print(f"✅ {region} - {len(records)} records, {len(status_codes)} status codes")

    collect(WIKI_URL, records, status_codes, globals=True)
    print(f"✅ {WIKI_URL} - {len(records)} records, {len(status_codes)} status codes")

    write_data(records, sorted(status_codes))  # Sort status codes before saving

def collect(url, records, status_codes, globals=False, retries=3):
    """Scrapes and collects data from the given Wikipedia page."""
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error fetching {url}: {e}")
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    else:
        print(f"❌ ERROR - Failed to fetch {url} after {retries} attempts")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select_one("#mw-content-text > .mw-parser-output")
    if not content:
        print(f"❌ ERROR - Empty content on {url}")
        return

    remove_cite_references(content)

    record_type = "Other"
    country_name, country_code = None, None

    for node in content.children:
        if not node.name or not node.get_text(strip=True):
            continue

        if node.name == "h2":
            section_name = node.get_text(strip=True)
            if section_name in ["See also", "External links", "National MNC Authorities"]:
                break
            record_type = {
                "National operators": "National",
                "Test networks": "Test",
                "International operators": "International"
            }.get(section_name, "Other")

        if node.name == "h4":
            parts = node.get_text(strip=True).split("–")
            if len(parts) == 2:
                country_name, country_code = parts[0].strip(), parts[1].strip()

        if node.name == "table" and not (globals and record_type == "National"):
            rows = node.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue

                status = cleanup(cols[4].get_text())
                if status:
                    status_codes.add(status)

                records.append({
                    "type": record_type,
                    "countryName": country_name,
                    "countryCode": country_code,
                    "mcc": cleanup(cols[0].get_text()),
                    "mnc": cleanup(cols[1].get_text()),
                    "brand": cleanup(cols[2].get_text()),
                    "operator": cleanup(cols[3].get_text()),
                    "status": status,
                    "bands": cleanup(cols[5].get_text()),
                    "notes": cleanup(cols[6].get_text())
                })

def write_data(records, status_codes):
    """Writes fetched data to JSON files."""
    with open(MCC_MNC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"✅ MCC-MNC list saved to {MCC_MNC_OUTPUT_FILE} ({len(records)} records)")

    with open(STATUS_CODES_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(status_codes, f, indent=2, ensure_ascii=False)
    print(f"✅ Status codes saved to {STATUS_CODES_OUTPUT_FILE} ({len(status_codes)} codes)")

def remove_cite_references(nodes):
    """Removes Wikipedia citation links."""
    for link in nodes.find_all("a", href=True):
        if link["href"].startswith("#cite_note"):
            link.decompose()

def cleanup(text):
    """Cleans up text by removing citations, unnecessary brackets, and extra spaces."""
    text = text.strip()
    text = re.sub(r'\[citation needed\]', '', text)
    text = re.sub(r'“', '"', text)
    text = re.sub(r'\[.*?\]$', '', text)  # Remove trailing brackets

    return text if text else None

if __name__ == "__main__":
    fetch()
