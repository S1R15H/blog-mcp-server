import os
from typing import Optional

# Ensure the environment variable is set before importing the server
RSS_FEED_URL = os.environ.get("RSS_FEED_URL")
if not RSS_FEED_URL:
    print("[WARN] RSS_FEED_URL is not set. Export it first or edit main_server.py.")

from main_server import (
    list_blog_posts,
    get_recent_posts,
    get_blog_post,
    get_blog_info,
    search_full_text,
)


def pick_first_slug(posts) -> Optional[str]:
    for p in posts:
        slug = p.get("slug")
        if slug:
            return slug
    return None


def main():
    print("=== Local Tool Smoke Test ===")
    print("RSS_FEED_URL:", os.environ.get("RSS_FEED_URL"))

    # 1) Blog info
    try:
        info = get_blog_info()
        print("[get_blog_info] ->", info)
    except Exception as e:
        print("[get_blog_info] ERROR:", e)

    # 2) List posts
    try:
        posts = list_blog_posts()
        print(f"[list_blog_posts] -> {len(posts)} posts")
        if posts[:3]:
            print("First 3:")
            for p in posts[:3]:
                print(" -", p.get("title"), "|", p.get("pubDate"), "|", p.get("slug"))
    except Exception as e:
        print("[list_blog_posts] ERROR:", e)
        posts = []

    # 3) Recent posts (reversed feed order)
    try:
        recent = get_recent_posts(3)
        print("[get_recent_posts] ->")
        for p in recent:
            print(" -", p.get("title"), "|", p.get("pubDate"), "|", p.get("slug"))
    except Exception as e:
        print("[get_recent_posts] ERROR:", e)

    # 4) Fetch one post content
    try:
        slug = pick_first_slug(recent or posts)
        if slug:
            post = get_blog_post(slug)
            content = post.get("content", "")
            print("[get_blog_post] slug:", slug)
            print("Content length:", len(content))
            print("Preview:\n", content[:800])
        else:
            print("[get_blog_post] No slug available to test.")
    except Exception as e:
        print("[get_blog_post] ERROR:", e)

    # 5) Search full text on-demand (no index)
    try:
        q = os.environ.get("TEST_SEARCH_QUERY", "the")
        print(f"[search_full_text] Query: '{q}'")
        results = search_full_text(q)
        print(f"[search_full_text] -> {len(results)} hits")
        for r in results[:3]:
            print(" -", r.get("title"), "=>", r.get("snippet"))
    except Exception as e:
        print("[search_full_text] ERROR:", e)


if __name__ == "__main__":
    main()
