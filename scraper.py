import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime, format_datetime
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace


# ============================================================
# SETTINGS
# ============================================================

SOURCE_URL = "https://news.met.police.uk/tag/counter-terrorism-command"

BASE_URL = "https://news.met.police.uk"

# CHANGE THIS TO YOUR GITHUB PAGES ADDRESS
RSS_URL = "https://greydog395.github.io/met-police-rss/feed.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; MetPoliceRSS/1.0)"
    )
}


# ============================================================
# RSS NAMESPACE
# ============================================================

ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"

register_namespace(
    "atom",
    ATOM_NAMESPACE
)


# ============================================================
# DOWNLOAD PAGE
# ============================================================

def download_page():

    print("Downloading Met Police page...")

    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    print("Download successful.")

    return response.text


# ============================================================
# FIND ARTICLES
# ============================================================

def scrape_articles(page):

    soup = BeautifulSoup(
        page,
        "html.parser"
    )

    articles = []

    seen_urls = set()

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

        url = urljoin(
            BASE_URL,
            href
        )

        # Only Met Police pages
        if not url.startswith(BASE_URL):
            continue

        # Only news articles
        if "/news/" not in url:
            continue

        # Remove duplicate links
        if url in seen_urls:
            continue

        seen_urls.add(url)

        articles.append({
            "title": title,
            "url": url
        })

    print(
        f"Found {len(articles)} articles."
    )

    return articles


# ============================================================
# GET ARTICLE INFORMATION
# ============================================================

def get_article_details(article):

    print(
        "Reading:",
        article["title"]
    )

    try:

        response = requests.get(
            article["url"],
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # ----------------------------------------------------
        # FIND PUBLICATION DATE
        # ----------------------------------------------------

        publication_date = None

        # First try <time>
        time_element = soup.find("time")

        if time_element:

            date_value = (
                time_element.get("datetime")
                or time_element.get_text(
                    " ",
                    strip=True
                )
            )

            if date_value:

                try:

                    publication_date = (
                        parsedate_to_datetime(
                            date_value
                        )
                    )

                except Exception:

                    try:

                        publication_date = (
                            datetime.fromisoformat(
                                date_value.replace(
                                    "Z",
                                    "+00:00"
                                )
                            )
                        )

                    except Exception:
                        pass

        # ----------------------------------------------------
        # TRY META TAGS
        # ----------------------------------------------------

        if publication_date is None:

            meta_names = [
                "article:published_time",
                "date",
                "pubdate",
                "publishdate"
            ]

            for name in meta_names:

                element = soup.find(
                    "meta",
                    attrs={
                        "property": name
                    }
                )

                if element is None:

                    element = soup.find(
                        "meta",
                        attrs={
                            "name": name
                        }
                    )

                if element:

                    value = element.get(
                        "content"
                    )

                    if value:

                        try:

                            publication_date = (
                                datetime.fromisoformat(
                                    value.replace(
                                        "Z",
                                        "+00:00"
                                    )
                                )
                            )

                            break

                        except Exception:
                            pass

        # ----------------------------------------------------
        # FIND DESCRIPTION
        # ----------------------------------------------------

        description = ""

        meta_description = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta_description:

            description = (
                meta_description.get(
                    "content",
                    ""
                ).strip()
            )

        # ----------------------------------------------------
        # FALLBACK DATE
        # ----------------------------------------------------

        if publication_date is None:

            publication_date = datetime.now(
                timezone.utc
            )

        # Make sure the date has timezone
        if publication_date.tzinfo is None:

            publication_date = (
                publication_date.replace(
                    tzinfo=timezone.utc
                )
            )

        return {
            "title": article["title"],
            "url": article["url"],
            "description": description,
            "publication_date": publication_date
        }

    except Exception as error:

        print(
            "Could not read article:",
            error
        )

        # Still return the article
        # so one failure doesn't stop
        # the entire RSS feed.

        return {
            "title": article["title"],
            "url": article["url"],
            "description": article["title"],
            "publication_date": datetime.now(
                timezone.utc
            )
        }


# ============================================================
# CREATE RSS FEED
# ============================================================

def create_rss(articles):

    rss = Element(
        "rss",
        {
            "version": "2.0"
        }
    )

    channel = SubElement(
        rss,
        "channel"
    )

    # --------------------------------------------------------
    # CHANNEL TITLE
    # --------------------------------------------------------

    title = SubElement(
        channel,
        "title"
    )

    title.text = (
        "Met Police - "
        "Counter Terrorism Command"
    )

    # --------------------------------------------------------
    # CHANNEL LINK
    # --------------------------------------------------------

    link = SubElement(
        channel,
        "link"
    )

    link.text = SOURCE_URL

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = SubElement(
        channel,
        "description"
    )

    description.text = (
        "Latest Metropolitan Police news "
        "stories tagged Counter Terrorism Command."
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = SubElement(
        channel,
        "language"
    )

    language.text = "en-GB"

    # --------------------------------------------------------
    # LAST BUILD DATE
    # --------------------------------------------------------

    last_build_date = SubElement(
        channel,
        "lastBuildDate"
    )

    last_build_date.text = format_datetime(
        datetime.now(timezone.utc)
    )

    # --------------------------------------------------------
    # ATOM SELF LINK
    # --------------------------------------------------------

    atom_link = SubElement(
        channel,
        f"{{{ATOM_NAMESPACE}}}link"
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

    # --------------------------------------------------------
    # ARTICLES
    # --------------------------------------------------------

    for article in articles:

        item = SubElement(
            channel,
            "item"
        )

        # Title
        item_title = SubElement(
            item,
            "title"
        )

        item_title.text = article["title"]

        # Link
        item_link = SubElement(
            item,
            "link"
        )

        item_link.text = article["url"]

        # GUID
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

        item_description.text = (
            article["description"]
        )

        # Publication date
        pub_date = SubElement(
            item,
            "pubDate"
        )

        pub_date.text = format_datetime(
            article["publication_date"]
        )

    return rss


# ============================================================
# SAVE RSS
# ============================================================

def save_rss(rss):

    print("Creating feed.xml...")

    tree = ElementTree(
        rss
    )

    tree.write(
        "feed.xml",
        encoding="utf-8",
        xml_declaration=True
    )

    print(
        "feed.xml created successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # Download category page
    page = download_page()

    # Find articles
    articles = scrape_articles(
        page
    )

    if not articles:

        print(
            "ERROR: No articles found."
        )

        return

    # Get details from each article
    detailed_articles = []

    for article in articles:

        details = get_article_details(
            article
        )

        detailed_articles.append(
            details
        )

    # Sort newest first
    detailed_articles.sort(
        key=lambda x: x["publication_date"],
        reverse=True
    )

    # Create RSS
    rss = create_rss(
        detailed_articles
    )

    # Save RSS
    save_rss(
        rss
    )

    print()
    print(
        "================================"
    )
    print(
        "RSS SCRAPER FINISHED"
    )
    print(
        "================================"
    )
    print(
        f"Articles: {len(detailed_articles)}"
    )
    print(
        "File: feed.xml"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
