import hashlib
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.miyakoshi-holdings.com"
MAX_PAGES = 50
CRAWL_DELAY = 1.0
HEADERS = {
    "User-Agent": "miyakoshi-watch/1.0 (+https://github.com/miyakoshi-watch)"
}


def load_robots(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    rp.set_url(urljoin(base_url, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        pass
    return rp


def fetch_page(url: str, session: requests.Session) -> str | None:
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"[WARN] fetch failed: {url} -> {e}")
        return None


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            clean = parsed._replace(fragment="").geturl()
            links.append(clean)
    return list(set(links))


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def crawl(base_url: str = BASE_URL, max_pages: int = MAX_PAGES) -> dict[str, dict]:
    """
    Returns:
        { url: { "hash": str, "text": str } }
    """
    rp = load_robots(base_url)
    session = requests.Session()

    visited: dict[str, dict] = {}
    queue = [base_url]

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        if not rp.can_fetch(HEADERS["User-Agent"], url):
            print(f"[INFO] robots.txt disallows: {url}")
            continue

        html = fetch_page(url, session)
        if html is None:
            continue

        text = extract_text(html)
        visited[url] = {
            "hash": hash_text(text),
            "text": text,
        }
        print(f"[OK] crawled ({len(visited)}/{max_pages}): {url}")

        for link in extract_links(html, base_url):
            if link not in visited and link not in queue:
                queue.append(link)

        time.sleep(CRAWL_DELAY)

    return visited
