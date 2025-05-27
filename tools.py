from langchain.tools import Tool
from datetime import datetime
import requests
from bs4 import BeautifulSoup


# ========== Save Tool ==========

def save_to_txt(data: str, filename: str = "contract_output.txt") -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Contract Summary ---\nTimestamp: {timestamp}\n\n{data}\n\n"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(formatted_text)
    
    return f"Data successfully saved to {filename}"


save_tool = Tool(
    name="save_text_to_file",
    func=save_to_txt,
    description="Saves structured contract summary to a text file."
)


# ========== SEC Fetch Tool ==========

HEADERS = {
    "User-Agent": "Syntax AI syntax@example.com"
}


def get_cik(ticker: str) -> str:
    url = "https://www.sec.gov/files/company_tickers.json"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    for entry in data.values():
        if entry['ticker'].lower() == ticker.lower():
            return str(entry['cik_str']).zfill(10)
    raise ValueError("CIK not found for ticker")


def get_latest_filing_url(cik: str, form_type: str = "10-K") -> str:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    res = requests.get(url, headers=HEADERS)
    filings = res.json().get("filings", {}).get("recent", {})
    for i, ftype in enumerate(filings.get("form", [])):
        if ftype == form_type:
            accession = filings["accessionNumber"][i].replace("-", "")
            return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/index.html"
    raise ValueError("Filing not found")


def extract_text_from_sec_filing(index_url: str) -> str:
    res = requests.get(index_url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.find_all("a")

    # Filter links that are actual documents (not SEC index pages)
    candidate_links = [
        link.get("href", "")
        for link in links
        if link.get("href", "").endswith(".htm")
        and not link.get("href", "").startswith("/index.htm")
        and "Archives" in link.get("href", "")
    ]

    if not candidate_links:
        raise ValueError("No valid .htm document links found in filing")

    # Prefer EX-10 exhibit (contract), fallback to first .htm
    preferred = [l for l in candidate_links if "ex10" in l.lower() or "def14a" in l.lower()]
    selected = preferred[0] if preferred else candidate_links[0]

    full_url = f"https://www.sec.gov{selected}"
    print(f"Fetching actual filing from: {full_url}")

    doc_res = requests.get(full_url, headers=HEADERS)
    doc_soup = BeautifulSoup(doc_res.text, "html.parser")
    return doc_soup.get_text(separator=" ", strip=True)


def fetch_contract_text(ticker: str, form_type: str = "10-K") -> str:
    cik = get_cik(ticker)
    filing_url = get_latest_filing_url(cik, form_type)
    text = extract_text_from_sec_filing(filing_url)
    print("=== SEC Filing Text Preview ===")
    print(text[:2000])  # Show first 2K characters
    return text[:5000]


fetch_sec_contract_tool = Tool.from_function(
    func=fetch_contract_text,
    name="fetch_sec_contract",
    description="Fetches the text of the latest SEC filing (e.g., 10-K, DEF 14A) for a given company ticker symbol."
)