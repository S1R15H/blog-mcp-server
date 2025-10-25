# Blog RSS MCP Server

A small FastMCP-based service exposing two tools for working with a blog RSS feed:

# Blog RSS MCP Server

A minimal Model Context Protocol (MCP) server that exposes tools for working with a blog’s RSS/Atom feed. It lists posts, fetches post content, returns recent posts, basic blog info, and can search post content on-demand.

## What’s in here

- `main_server.py` — MCP server with tools:
	- `list_blog_posts()` → [{title, slug (url), pubDate}]
	- `get_blog_post(slug)` → {slug, url, content} (content extracted from page HTML, preferring <article>)
	- `get_recent_posts(count=5)` → recent posts (simple reverse order)
	- `get_blog_info()` → blog metadata
	- `search_full_text(query)` → on-demand search (fetches each post and searches the text directly)
- `run_local_tests.py` — quick local smoke test that exercises the tools without starting the MCP server.
- `Dockerfile` — container image for running the server.
- `requirements.txt` — Python dependencies.

## Requirements

- Python 3.10+
- Recommended: a virtual environment (e.g., `.venv`)

Install dependencies:

```bash
pip install -r requirements.txt
```

Note for Python 3.13+: `feedparser` imports the removed stdlib module `cgi`; this repo includes `python-legacy-cgi` in requirements to ensure compatibility.

## Configuration

Set environment variables as needed:

- `RSS_FEED_URL` (required) → Full URL to your RSS/Atom feed (e.g., `https://example.com/feed.xml`)
- `MCP_TRANSPORT` (optional) → `stdio` (default), `sse`, or `streamable-http`
- `MCP_MOUNT_PATH` (optional) → mount path for applicable transports

Example:

```bash
export RSS_FEED_URL="https://www.sirishgurung.com/rss.xml"
export MCP_TRANSPORT=stdio
```

## Run locally (MCP server)

```bash
python main_server.py
```

With a venv:

```bash
.venv/bin/python main_server.py
```

## Local smoke test (no MCP client required)

```bash
.venv/bin/python run_local_tests.py
```

That script will print blog info, list posts, fetch one post’s content, and run a simple on-demand search.

## Docker

Build the image:

```bash
docker build -t blog-rss-mcp:latest .
```

Run with stdio transport (for MCP clients that spawn the container and talk over stdio):

```bash
docker run --rm -i \
	-e RSS_FEED_URL="https://www.sirishgurung.com/rss.xml" \
	-e MCP_TRANSPORT=stdio \
	blog-rss-mcp:latest
```

Run with basic HTTP transport (optional):

```bash
docker run -d \
	-e RSS_FEED_URL="https://www.sirishgurung.com/rss.xml" \
	-e MCP_TRANSPORT=streamable-http \
	-e MCP_MOUNT_PATH="/mcp" \
	-p 5000:5000 \
	--name blog-rss-mcp \
	blog-rss-mcp:latest
```

## Notes & troubleshooting

- Logs go to stderr; stdio transport messages go to stdout (safe for MCP clients).
- If HTTPS feed fetches fail in a minimal base image, install system CA certificates in your container.
- If `mcp.run()` signature changes between versions, inspect `FastMCP.run` in your installed package and adjust the call accordingly.

Example:

```bash
export RSS_FEED_URL="https://www.sirishgurung.com/rss.xml"
export MCP_TRANSPORT=stdio

```

## Running locally

Start the server directly with Python (development):

```bash
python main_server.py
```

If `MCP_TRANSPORT=stdio`, the process runs attached to STDIN/STDOUT so a supervising client can manage lifecycle and communicate over stdio.

## Docker

Build the image locally:

```bash
docker buildx build -f Dockerfile -t blog-rss-mcp:latest --load .
```

Run attached to your terminal (stdio transport):

```bash
docker run --rm -i \
	-e RSS_FEED_URL="https://www.sirishgurung.com/rss.xml" \
	-e MCP_TRANSPORT=stdio \
	--name blog-rss-mcp blog-rss-mcp:latest
```

Or run detached with an HTTP/streamable transport (adjust ports as needed):

```bash
docker run -d \
	-e RSS_FEED_URL="https://www.sirishgurung.com/rss.xml" \
	-e MCP_TRANSPORT=streamable-http \
	-e MCP_MOUNT_PATH="/mcp" \
	-p 5000:5000 \
	--name blog-rss-mcp blog-rss-mcp:latest
```

## Search

- `search_full_text(query)` performs a simple case-insensitive substring search on-demand. It fetches each post’s content live and extracts plain text, so results always reflect the current site content.

## Custom catalog and client integration

- The repo includes `custom_catalog_for_blog_mcp.txt` (example YAML you can copy into a client catalog). Use `MCP_TRANSPORT=stdio` when you want the client to spawn the container and communicate over stdio.

## Troubleshooting

- If you see import errors for `feedparser` or `beautifulsoup4`, run `pip install -r requirements.txt` in the same environment.
- If posts are missing from `list_blog_posts()`, verify the feed provides `published` or `pubDate`; the server is defensive but you can inspect the raw parsed feed:

```python
import feedparser
f = feedparser.parse("https://your-blog.example.com/feed.xml")
print(f.feed)
print(len(f.entries), f.entries[0].keys())
```

- If `mcp.run()` fails due to signature mismatch, inspect `mcp.server.fastmcp.FastMCP.run` in your installed package and adjust the call in `main_server.py`.

## Development & tests

- Add pytest tests that mock `feedparser.parse` to exercise `list_blog_posts`, `get_blog_post`, and `search_full_text`.
- Consider adding a GitHub Actions workflow to run tests on push.

## Security & production notes

- Do not expose the server publicly without authentication or a reverse proxy with TLS.
- When building/persisting indexes, secure the storage and limit who can trigger a rebuild.

## Next steps I can help with

- Wire `_build_fulltext_index()` to run at startup when `BUILD_FULLTEXT_INDEX` is enabled (optionally persist to disk).
- Add unit tests and a CI workflow.
- Add a `HEALTHCHECK` to the Dockerfile and/or a small HTTP health endpoint.

Tell me which of those you'd like and I'll implement it.
