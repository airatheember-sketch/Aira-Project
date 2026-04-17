import feedparser
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from core.auth import get_current_user

router = APIRouter(prefix="/news", tags=["news"])

# ── RSS Feed Sources ──────────────────────────────────────────────────────────
FEEDS = {
    "general":   "https://feeds.bbci.co.uk/news/rss.xml",
    "world":     "https://feeds.bbci.co.uk/news/world/rss.xml",
    "tech":      "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "business":  "https://feeds.bbci.co.uk/news/business/rss.xml",
    "science":   "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "health":    "https://feeds.bbci.co.uk/news/health/rss.xml",
    "pakistan":  "https://www.dawn.com/feeds/home",
}

DEFAULT_LIMIT = 5
MAX_LIMIT = 15


@router.get("/headlines")
async def get_headlines(
    category: str = Query("general", description="Category: general, world, tech, business, science, health, pakistan"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch latest headlines from RSS feed.
    Returns list of { title, summary, link, published }
    """
    feed_url = FEEDS.get(category.lower(), FEEDS["general"])

    try:
        # Fetch RSS feed asynchronously
        async with httpx.AsyncClient() as client:
            response = await client.get(
                feed_url,
                timeout=10.0,
                headers={"User-Agent": "AIRA/1.0"}
            )
            response.raise_for_status()
            raw_feed = response.text

        # Parse with feedparser
        feed = feedparser.parse(raw_feed)

        if not feed.entries:
            raise HTTPException(status_code=404, detail=f"No headlines found for category: {category}")

        headlines = []
        for entry in feed.entries[:limit]:
            headlines.append({
                "title":     entry.get("title", "No title"),
                "summary":   _clean_summary(entry.get("summary", "")),
                "link":      entry.get("link", ""),
                "published": entry.get("published", ""),
                "source":    feed.feed.get("title", "Unknown")
            })

        return {
            "category": category,
            "count": len(headlines),
            "headlines": headlines
        }

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Could not reach news source: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News fetch error: {str(e)}")


def _clean_summary(text: str) -> str:
    """Strip HTML tags from summary text."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()[:300]  # cap at 300 chars