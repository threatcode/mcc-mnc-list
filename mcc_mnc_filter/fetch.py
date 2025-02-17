import json
import os
import re
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

def fetch():
    records = []
    status_codes = []
    
    for region in WIKI_URL_REGIONS:
        collect(region, records, status_codes)
        print(region, len(records), len(status_codes))
    
    collect(WIKI_URL, records, status_codes, globals=True)
    print(WIKI_URL, len(records), len(status_codes))
    
    write_data(records, status_codes)

def collect(url, records, status_codes, globals=False):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"ERROR - Failed to fetch {url}")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select_one("#mw-content-text > .mw-parser-output")
    
    if not content:
        print("ERROR - empty content")
        return
    
    remove_cite_references(content)
    
    record_type = "other"
    section_name = None
    country_name = None
    country_code = None
    
    for node in content.children:
        if not node.name or not node.get_text(strip=True):
            continue

        if node.name == "h2":
            section_name = node.get_text(strip=True)
            if section_name in ["See also", "External links", "National MNC Authorities"]:
                break
            if section_name == "National operators":
                record_type = "National"
            elif section_name == "Test networks":
                record_type = "Test"
            elif section_name == "International operators":
                record_type = "International"
        
        if node.name == "h4":
            country_text = node.get_text(strip=True)
            parts = country_text.split("–")
            if len(parts) == 2:
                country_name, country_code = parts[0].strip(), parts[1].strip()
        
        if node.name == "table":
            if globals and record_type == "National":
                continue
            
            rows = node.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue
                
                status = cleanup(cols[4].get_text())
                if status and status not in status_codes:
                    status_codes.append(status)
                
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
    with open(MCC_MNC_OUTPUT_FILE, "w") as f:
        json.dump(records, f, indent=2)
    print(f"MCC-MNC list saved to {MCC_MNC_OUTPUT_FILE}")
    print(f"Total {len(records)} records")
    
    status_codes.sort()
    with open(STATUS_CODES_OUTPUT_FILE, "w") as f:
        json.dump(status_codes, f, indent=2)
    print(f"Status codes saved to {STATUS_CODES_OUTPUT_FILE}")

def remove_cite_references(nodes):
    for link in nodes.find_all("a", href=True):
        if link["href"].startswith("#cite_note"):
            link.decompose()

def cleanup(text):
    text = text.strip()
    text = remove_citation_needed(text)
    text = re.sub(r'“', '"', text)
    text = re.sub(r'\[citation needed\]', '', text)
    if text.startswith("[") and text.endswith("]"):
        return None
    if text.endswith("]"):
        text = re.sub(r'\[.*\]$', '', text).strip()
    return text if text else None

def remove_citation_needed(text):
    return re.sub(r'\[citation needed\]', '', text)

if __name__ == "__main__":
    fetch()
