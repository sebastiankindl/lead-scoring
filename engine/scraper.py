import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {"User-Agent": "LeadIntelligenceBot/1.0"}

def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"

def fetch_html(url: str, timeout: int = 8, headers=None) -> str:
    headers = headers or DEFAULT_HEADERS
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def extract_context_texts(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.get_text(" ", strip=True) if soup.title else "")
    h1 = " ".join([h.get_text(" ", strip=True) for h in soup.find_all("h1")])

    # footer
    footer_tag = soup.find("footer")
    footer = footer_tag.get_text(" ", strip=True) if footer_tag else ""

    # body = whole text minus footer
    full_text = soup.get_text(" ", strip=True)
    body = full_text.replace(footer, "") if footer else full_text

    # optional: simple heuristics for product-pages (e.g. urls with product/solutions)
    return {
        "title": title.lower(),
        "h1": h1.lower(),
        "body": body.lower(),
        "footer": footer.lower(),
    }
