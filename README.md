# Brightwave Web Crawler

A lightweight, multi-threaded web crawler with search capabilities built entirely with Python's standard library. No external crawling or parsing libraries — just `urllib`, `html.parser`, `threading`, and `queue`.

## Features

- **Index**: Crawl from any URL up to depth `k` with configurable parameters
- **Search**: Query indexed pages and get `(relevant_url, origin_url, depth)` triples
- **Back-Pressure**: Bounded queue + rate limiting to prevent system overload
- **Multi-Threaded**: Configurable worker threads per crawl job
- **Real-Time Dashboard**: Monitor active crawlers, queue depth, back-pressure drops
- **Resume Support**: Visited URLs persist to disk — survives restarts
- **Modern UI**: Dark-themed web interface with live-updating dashboard

## Quick Start

```bash
# 1. Clone and enter the project
cd google

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python3 app.py

# 4. Open in browser
open http://localhost:5050
```

## Architecture

```
google/
├── app.py                      # Flask server & API endpoints
├── services/
│   ├── crawler_service.py      # CrawlerJob thread + HTML parser
│   └── search_service.py       # File-based search engine
├── utils/
│   └── storage.py              # Thread-safe visited URL storage (with persistence)
├── demo/
│   ├── crawler.html/js         # Crawl initiation page
│   ├── status.html/js          # Real-time dashboard
│   ├── search.html/js          # Search interface with pagination
│   └── style.css               # Dark-themed design system
├── data/
│   ├── storage/                # Word index files (A.data, B.data, ...)
│   └── visited_urls.data       # Persisted visited URLs (resume support)
├── requirements.txt
├── product_prd.md
└── recommendation.md
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/crawl` | POST | Start a new crawl job |
| `/api/status` | GET | System status + per-crawler details |
| `/api/search?query=...` | GET | Search indexed pages |

### POST `/api/crawl`

```json
{
  "origin": "https://example.com",
  "depth": 2,
  "hit_rate": 5.0,
  "max_queue_capacity": 1000,
  "num_workers": 4
}
```

### GET `/api/status` Response

```json
{
  "visited_urls_count": 150,
  "active_crawlers_count": 1,
  "status": "Running",
  "crawlers": [
    {
      "crawler_id": "1711234567_12345",
      "origin": "https://example.com",
      "is_running": true,
      "pages_crawled": 42,
      "queue_size": 120,
      "queue_capacity": 1000,
      "back_pressure_drops": 3,
      "errors": 1,
      "elapsed_seconds": 15.2
    }
  ]
}
```

### GET `/api/search?query=technology` Response

```json
{
  "results": [
    {
      "relevant_url": "https://example.com/tech",
      "origin_url": "https://example.com",
      "depth": 1,
      "freq": 12
    }
  ]
}
```

## How It Works

### Indexing

1. User submits a URL and depth `k` via the web UI
2. A `CrawlerJob` thread is created with a bounded `queue.Queue`
3. Multiple worker threads pull URLs from the shared queue
4. Each page is fetched via `urllib.request` and parsed using `HTMLParser`
5. Words are extracted, counted, and saved to letter-indexed files (`A.data`, `B.data`, etc.)
6. Discovered links are enqueued if within depth limit and not already visited
7. **Back-pressure**: If queue is full, new links are dropped (`put_nowait`)
8. **Rate limiting**: Workers sleep `1/hit_rate` seconds between requests

### Searching

1. User enters a query (single or multi-word)
2. Each word is looked up in its corresponding letter file
3. Results are aggregated by URL and sorted by total word frequency
4. Returns `(relevant_url, origin_url, depth)` triples

### Resume After Interruption

- Every visited URL is appended to `data/visited_urls.data`
- On restart, the storage module loads this file automatically
- Previously visited URLs are skipped, avoiding redundant crawling

## Design Decisions

| Decision | Rationale |
|---|---|
| `stdlib` only for crawling/parsing | Assignment requirement — no BeautifulSoup, Scrapy, etc. |
| File-based word index | Simple, no DB dependency, supports concurrent read/write |
| `queue.Queue(maxsize=N)` | Built-in back-pressure via bounded queue |
| `put_nowait()` for enqueue | Non-blocking — drops links when queue is full instead of blocking |
| Letter-indexed files | Partitions data for faster lookup (only scan relevant letter file) |
| `threading.Lock` for writes | Prevents file corruption from concurrent worker writes |
| Daemon threads | Automatic cleanup when main process exits |

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: Vanilla HTML/CSS/JS (no frameworks)
- **Storage**: File-based (no external database)
- **Crawling**: `urllib.request`, `html.parser` (Python stdlib)
- **Concurrency**: `threading`, `queue` (Python stdlib)
