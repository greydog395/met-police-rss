import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree


# ============================================================
# SETTINGS
# ============================================================

SOURCE_URL = "https://news.met.police.uk/tag/counter-terrorism-command"

BASE_URL = "https://news.met.police.uk"

# CHANGE THIS
# Put your GitHub username and repository name here.
RSS_URL = "https://greydog395.github.io/met-police-rss/feed.xml"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; MetPoliceRSS/1.0)"
    )
}


# ============================================================
# DOWNLOAD THE MET POLICE PAGE
# ============================================================

def download_page():

    print("Downloading Met Police page...")

    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    print("Page downloaded successfully.")

    return response.text


# ============================================================
# SCRAPE ARTICLES
# ============================================================

def scrape_articles(page):

    soup = BeautifulSoup(
        page,
        "html.parser"
    )

    articles = []

    seen_urls = set()

    # Find all links on the page
    for link in soup.find_all("a", href=True):

        title = link.get_text(
            " ",
            strip=True
        )

        href = link.get("href")

        if not title:
            continue

        if not href:
            continue

        # Convert relative URLs into full URLs
        url = urljoin(
            BASE_URL,
            href
        )

        # Only keep Met Police links
        if not url.startswith(BASE_URL):
            continue

        # Only keep news articles
        if "/news/" not in url:
            continue

        # Avoid duplicates
        if url in seen_urls:
            continue

        seen_urls.add(url)

        articles.append({
            "title": title,
            "url": url
        })

    print(
        f"Found {len(articles)} possible articles."
    )

    return articles


# ============================================================
# CREATE RSS FEED
# ============================================================

def create_rss(articles):

    rss = Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": (
                "http://www.w3.org/2005/Atom"
            )
        }
    )

    channel = SubElement(
        rss,
        "channel"
    )

    # Feed title
    title = SubElement(
        channel,
        "title"
    )

    title.text = (
        "Met Police - "
        "Counter Terrorism Command"
    )

    # Feed website
    link = SubElement(
        channel,
        "link"
    )

    link.text = SOURCE_URL

    # Feed description
    description = SubElement(
        channel,
        "description"
    )

    description.text = (
        "Latest Metropolitan Police news "
        "stories tagged Counter Terrorism Command."
    )

    # Language
    language = SubElement(
        channel,
        "language"
    )

    language.text = "en-GB"

    # Last updated time
    last_build_date = SubElement(
        channel,
        "lastBuildDate"
    )

    last_build_date.text = format_datetime(
        datetime.now(timezone.utc)
    )

    # RSS self-reference
    atom_link = SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link"
    )

    atom_link.set(
        "href",
        RSS_URL
    )

    atom_link.set(
        "rel",
        "self"
    )

    atom_link.set(
        "type",
        "application/rss+xml"
    )

    # ========================================================
    # ADD ARTICLES
    # ========================================================

    for article in articles:

        item = SubElement(
            channel,
            "item"
        )

        # Article title
        item_title = SubElement(
            item,
            "title"
        )

        item_title.text = article["title"]

        # Article URL
        item_link = SubElement(
            item,
            "link"
        )

        item_link.text = article["url"]

        # Unique ID
        guid = SubElement(
            item,
            "guid"
        )

        guid.set(
            "isPermaLink",
            "true"
        )

        guid.text = article["url"]

        # Description
        item_description = SubElement(
            item,
            "description"
        )

        item_description.text = article["title"]

        # Publication date
        pub_date = SubElement(
            item,
            "pubDate"
        )

        pub_date.text = format_datetime(
            datetime.now(timezone.utc)
        )

    return rss


# ============================================================
# SAVE RSS FILE
# ============================================================

def save_rss(rss):

    print("Saving RSS feed...")

    tree = ElementTree(rss)

    tree.write(
        "feed.xml",
        encoding="utf-8",
        xml_declaration=True
    )

    print("RSS feed saved as feed.xml")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    page = download_page()

    articles = scrape_articles(
        page
    )

    if not articles:

        print(
            "WARNING: No articles were found."
        )

        return

    rss = create_rss(
        articles
    )

    save_rss(
        rss
    )

    print(
        "Scraping complete."
    )


if __name__ == "__main__":
    main()
