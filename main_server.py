import os
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Literal

# Configuration
# Set your blog's RSS feed URL via env or hardcode here.
RSS_FEED_URL = os.environ.get('RSS_FEED_URL', 'https://YOUR_BLOG_URL_HERE.com/feed.xml')

# Transport and mount path for FastMCP.run
MCP_TRANSPORT = os.environ.get('MCP_TRANSPORT', 'stdio')
MCP_MOUNT_PATH = os.environ.get('MCP_MOUNT_PATH', None) or None


# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP app (visible name to clients)
mcp = FastMCP("Blog RSS Server")

@mcp.tool()
def list_blog_posts() -> List[Dict[str, Any]]:
    """
    Parses the RSS feed to get a list of all posts.
    Returns a list of post objects, each with a 'title', 'slug' (which is the full URL), and 'pubdate'.
    """
    if RSS_FEED_URL == 'https://YOUR_BLOG_URL_HERE.com/feed.xml':
        raise RuntimeError("RSS_FEED_URL is not set. Please set the RSS_FEED_URL environment variable or edit main_server.py.")

    logger.info("Fetching posts from RSS feed: %s", RSS_FEED_URL)
    
    # Parse the feed and return simple post dicts
    try:
        feed = feedparser.parse(RSS_FEED_URL)
        if getattr(feed, 'bozo', False):
            logger.warning("Feed may be malformed. Error: %s", getattr(feed, 'bozo_exception', 'unknown'))

        posts = []
        entries = getattr(feed, 'entries', []) or []
        if not entries:
            logger.info("No entries found in RSS feed: %s", RSS_FEED_URL)
            return posts

        for entry in entries:
            post = _entry_to_post_dict(entry)
            slug = post.get('slug')
            title = post.get('title')
            if not slug or not title:
                logger.debug("Skipping malformed entry (missing title or link): %s", entry)
                continue
            posts.append(post)

        return posts
    except Exception as e:
        logger.error("Error parsing RSS feed: %s", e)
        raise Exception("Failed to parse RSS feed. Check your RSS_FEED_URL.") from e

@mcp.tool()
def get_blog_post(slug: str) -> Dict[str, str]:
    """
    Finds a specific post from the RSS feed and returns its content.
    The 'slug' parameter must be the post's full URL (which is returned by 'list_blog_posts').
    """
    if not slug:
        raise ValueError("Missing required parameter: slug (which should be the post's full URL)")

    logger.info("Fetching single post content via HTTP for: %s", slug)

    try:
        resp = requests.get(slug, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible; BlogRSS/1.0)"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text or '', 'html.parser')
        article = soup.find('article')
        if article and article.get_text(strip=True):
            text_content = article.get_text(separator="\n\n", strip=True)
        else:
            # Fallback: use full page/body text if <article> not present
            body = soup.body or soup
            text_content = body.get_text(separator="\n\n", strip=True)

        return {
            "slug": slug,
            "url": slug,
            "content": text_content
        }

    except Exception as e:
        logger.error("Error fetching or parsing post HTML: %s", e)
        # Re-raise the exception
        raise Exception(f"Failed to fetch post HTML. {e}") from e


def _entry_to_post_dict(entry) -> Dict[str, Any]:
    """Normalize a feed entry to a simple dict with title, slug and pubDate."""
    slug = getattr(entry, 'link', None) or (entry.get('link') if isinstance(entry, dict) else None)
    title = getattr(entry, 'title', None) or (entry.get('title') if isinstance(entry, dict) else None)
    pub = getattr(entry, 'published', None) or getattr(entry, 'pubDate', None) or (entry.get('published') if isinstance(entry, dict) else None)

    return {
        'title': title,
        'slug': slug,
        'pubDate': pub,
    }

@mcp.tool()
def get_recent_posts(count: int = 5) -> List[Dict[str, str]]:
    """Return the most recent `count` posts (by published date)."""
    # Simple behavior: RSS feeds often append newest items at the bottom.
    posts = list_blog_posts()
    # Reverse so newest (bottom) becomes first
    posts_sorted = list(reversed(posts))
    return posts_sorted[:max(1, int(count))]


@mcp.tool()
def get_blog_info() -> Dict[str, Any]:
    """Return blog-level metadata: title, subtitle/description, and link."""
    if RSS_FEED_URL == 'https://YOUR_BLOG_URL_HERE.com/feed.xml':
        raise RuntimeError("RSS_FEED_URL is not set. Please set the RSS_FEED_URL environment variable or edit main_server.py.")

    feed = feedparser.parse(RSS_FEED_URL)
    info = {}
    feed_info = getattr(feed, 'feed', {}) or {}
    info['title'] = getattr(feed_info, 'title', None) or (feed_info.get('title') if isinstance(feed_info, dict) else None)
    info['subtitle'] = getattr(feed_info, 'subtitle', None) or getattr(feed_info, 'description', None) or (feed_info.get('description') if isinstance(feed_info, dict) else None)
    info['link'] = getattr(feed_info, 'link', None) or (feed_info.get('link') if isinstance(feed_info, dict) else None)
    return info


@mcp.tool()
def search_full_text(query: str) -> List[Dict[str, Any]]:
    """Search post contents on-demand for the query and return matches with snippets.

    Returns a list of {slug, title, snippet} where snippet contains a short excerpt containing the query.
    """
    if not query:
        raise ValueError("Missing required parameter: query")

    q = query.lower()
    results: List[Dict[str, Any]] = []

    # Fetch posts list, then fetch each post content on-demand and search within it.
    posts = list_blog_posts()
    for p in posts:
        url = p.get('slug')
        title = p.get('title')
        if not url:
            continue
        try:
            post = get_blog_post(url)
            text = (post.get('content') or '')
        except Exception as e:
            logger.warning("Failed to fetch post for search %s: %s", url, e)
            continue

        text_lower = text.lower()
        idx = text_lower.find(q)
        if idx >= 0:
            start = max(0, idx - 60)
            end = min(len(text), idx + len(q) + 60)
            snippet = text[start:end].strip()
            results.append({'slug': url, 'title': title, 'snippet': snippet})

    return results


if __name__ == "__main__":
    # Start the MCP server using the configured transport and mount path.
    logger.info("Starting MCP server using transport=%s mount_path=%s", MCP_TRANSPORT, MCP_MOUNT_PATH)

    def _normalize_transport(x: str) -> Literal['stdio', 'sse', 'streamable-http']:
        if x == 'sse':
            return 'sse'
        if x == 'streamable-http':
            return 'streamable-http'
        return 'stdio'

    try:
        mcp.run(transport=_normalize_transport(MCP_TRANSPORT), mount_path=MCP_MOUNT_PATH)
    except TypeError:
        # Defensive fallback: try positional call
        logger.info("TypeError calling mcp.run with keywords, trying positional call")
        try:
            mcp.run(_normalize_transport(MCP_TRANSPORT), MCP_MOUNT_PATH)
        except Exception:
            logger.exception("Failed to start MCP server with positional call")
            raise
    except Exception:
        logger.exception("Failed to start MCP server")
        raise

