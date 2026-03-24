# Product Requirements Document (PRD)

## Project Overview

**Product**: Brightwave Web Crawler & Search Engine  
**Objective**: Build a single-machine web crawler that indexes web pages and provides search functionality, with real-time system visibility via a web-based dashboard.  
**Timeframe**: 3–5 hours  
**Technology Constraint**: Use language-native functionality (Python stdlib) for core crawling and parsing. No third-party crawling or HTML parsing libraries.

---

## Core Requirements

### 1. Index Capability

**Method**: `index(origin, k)`

| Parameter | Type | Description |
|---|---|---|
| `origin` | URL (string) | Starting URL for the web crawl |
| `k` | integer | Maximum depth (number of hops from origin) |

**Behavior**:
- Initiate a breadth-first web crawl starting from `origin`
- Follow discovered links up to `k` hops from the origin
- Never crawl the same page twice (deduplication)
- Designed for large-scale crawls on a single machine
- Support configurable back-pressure mechanisms:
  - **Maximum queue depth**: Bounded queue with configurable capacity
  - **Rate limiting**: Configurable requests per second (politeness delay)

**Additional Parameters** (configurable via UI):
- `hit_rate`: Maximum pages per second (default: 5.0)
- `max_queue_capacity`: Maximum URL queue size (default: 1000)
- `num_workers`: Number of concurrent worker threads (default: 4)

### 2. Search Capability

**Method**: `search(query)`

| Parameter | Type | Description |
|---|---|---|
| `query` | string | Search term(s) |

**Returns**: List of triples `(relevant_url, origin_url, depth)` where:
- `relevant_url`: URL of an indexed page relevant to the query
- `origin_url`: The origin URL passed to `/index` when this page was discovered
- `depth`: The depth parameter `k` at which the page was found

**Behavior**:
- Search works while indexing is still active (reflects new results in real-time)
- Supports multi-word queries (aggregates results across words)
- Results are sorted by relevance (word frequency)
- Includes pagination (10 results per page)

### 3. User Interface

A web-based UI with three pages:

| Page | Purpose |
|---|---|
| **Crawler** | Configure and start new crawl jobs |
| **Dashboard** | Real-time system monitoring |
| **Search** | Query indexed pages with paginated results |

**Dashboard must display**:
- Overall system status (Running / Idle)
- Number of active crawlers
- Total URLs crawled
- Per-crawler details: queue depth, pages crawled, back-pressure drops, errors, elapsed time

### 4. Resume After Interruption (Bonus)

- Visited URLs are persisted to disk (`data/visited_urls.data`)
- On server restart, previously visited URLs are automatically loaded
- Crawlers skip already-visited pages without re-fetching

---

## Technical Architecture

### Backend (Python)

| Component | File | Responsibility |
|---|---|---|
| API Server | `app.py` | Flask routes, crawler lifecycle management |
| Crawler Engine | `services/crawler_service.py` | Multi-threaded BFS crawl with back-pressure |
| Search Engine | `services/search_service.py` | File-based word index search |
| Storage | `utils/storage.py` | Thread-safe URL deduplication with persistence |

### Frontend (Vanilla HTML/CSS/JS)

| File | Purpose |
|---|---|
| `demo/crawler.html/js` | Crawl initiation form |
| `demo/status.html/js` | Live dashboard (polls every 2s) |
| `demo/search.html/js` | Search interface with pagination |
| `demo/style.css` | Dark-themed design system |

### Data Storage (File-based)

| File | Content |
|---|---|
| `data/storage/{A-Z}.data` | Word index, partitioned by first letter |
| `data/visited_urls.data` | Persisted set of visited URLs |

---

## Non-Functional Requirements

| Requirement | Implementation |
|---|---|
| **Scalability** | Multi-worker threads, bounded queue, rate limiting |
| **Thread Safety** | `threading.Lock` for all shared state access |
| **Back-Pressure** | `queue.Queue(maxsize=N)` + `put_nowait()` drops |
| **Politeness** | Configurable `time.sleep(1/hit_rate)` between requests |
| **Resilience** | Disk persistence enables resume after crash |
| **Observability** | Per-crawler metrics exposed via `/api/status` |

---

## Assumptions

1. Index is invoked before search (but search works during active indexing)
2. The crawl scale is large but fits on a single machine
3. Relevance is defined as exact word match, ranked by frequency
4. Only HTML pages are processed (non-HTML content types are skipped)
5. External URLs are followed (no same-domain restriction by default)
6. UTF-8 encoding is assumed for all pages
