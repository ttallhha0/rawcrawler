import urllib.request
from urllib.parse import urljoin
from html.parser import HTMLParser
import threading
import time
import queue
import re
import json
import os

# Import our thread-safe storage singleton
from utils.storage import db

# ──────────────────────────────────────────────
# SECTION 1: Custom HTML Parser (no BeautifulSoup)
# ──────────────────────────────────────────────
class CrawlerParser(HTMLParser):
    """Language-native HTML parser that extracts links and word frequencies."""

    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.words = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    # Convert relative URLs to absolute
                    full_url = urljoin(self.base_url, value)
                    if full_url.startswith('http'):
                        self.links.append(full_url)

    def handle_data(self, data):
        # Extract visible text, clean it, and add to word list
        text = data.strip()
        if text:
            # Only keep words longer than 2 characters, lowercased
            words = re.findall(r'[a-z]{2,}', text.lower())
            self.words.extend(words)


# ──────────────────────────────────────────────
# SECTION 2: Crawler Job (Background Worker Thread)
# ──────────────────────────────────────────────
class CrawlerJob(threading.Thread):
    """
    A background thread that performs a breadth-first web crawl
    starting from an origin URL up to a maximum depth k.
    
    Back-pressure is enforced via:
      - Bounded queue (maxsize) — new links are dropped when full
      - Rate limiting (hit_rate) — throttles requests per second
    """

    def __init__(self, crawler_id, origin, max_depth, hit_rate, max_queue_capacity, num_workers=4):
        super().__init__()
        self.daemon = True  # Thread dies when main app exits
        self.crawler_id = crawler_id
        self.origin = origin
        self.max_depth = max_depth
        self.hit_rate = hit_rate          # Max requests per second (throttling)
        self.num_workers = num_workers    # Number of concurrent worker threads
        self.max_queue_capacity = max_queue_capacity

        # BACK-PRESSURE: Bounded queue — rejects new URLs when full
        self.q = queue.Queue(maxsize=max_queue_capacity)

        # Seed the queue with the origin URL: (current_url, origin_url, depth)
        self.q.put((self.origin, self.origin, 0))
        self.is_running = True

        # Per-crawler statistics for dashboard visibility
        self.pages_crawled = 0
        self.errors = 0
        self.back_pressure_drops = 0
        self.start_time = None

    def get_status(self):
        """Return a snapshot of this crawler's current state."""
        elapsed = 0
        if self.start_time:
            elapsed = round(time.time() - self.start_time, 1)

        return {
            "crawler_id": self.crawler_id,
            "origin": self.origin,
            "max_depth": self.max_depth,
            "is_running": self.is_running,
            "pages_crawled": self.pages_crawled,
            "queue_size": self.q.qsize(),
            "queue_capacity": self.max_queue_capacity,
            "back_pressure_drops": self.back_pressure_drops,
            "errors": self.errors,
            "elapsed_seconds": elapsed,
            "num_workers": self.num_workers,
            "hit_rate": self.hit_rate
        }

    def _worker(self, worker_id):
        """Each worker thread executes this function, pulling jobs from the shared queue."""
        while self.is_running:
            try:
                current_url, origin_url, depth = self.q.get(timeout=10)
            except queue.Empty:
                break  # No new URLs for 10 seconds — worker exits

            # Skip if depth limit exceeded or page already visited
            if depth > self.max_depth or db.is_visited(current_url):
                self.q.task_done()
                continue

            # Thread-safe: mark URL as visited
            db.mark_visited(current_url)

            try:
                # Fetch page using Python's native urllib (no third-party HTTP libs)
                req = urllib.request.Request(current_url, headers={'User-Agent': 'BrightwaveBot/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    # Only process HTML content
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' not in content_type:
                        self.q.task_done()
                        continue

                    html_content = response.read().decode('utf-8', errors='ignore')

                    # Parse page to extract words and links
                    parser = CrawlerParser(base_url=current_url)
                    parser.feed(html_content)

                    # Save word frequencies to disk for the search engine
                    self.save_words(parser.words, current_url, origin_url, depth)
                    self.pages_crawled += 1

                    # If we haven't reached max depth, enqueue discovered links
                    if depth < self.max_depth:
                        for link in parser.links:
                            if not db.is_visited(link):
                                try:
                                    # put_nowait: Back-pressure — raises Full immediately if queue is at capacity
                                    self.q.put_nowait((link, self.origin, depth + 1))
                                except queue.Full:
                                    # Queue is full — dropping this link (back-pressure protection)
                                    self.back_pressure_drops += 1

            except Exception as e:
                self.errors += 1
                print(f"[{self.crawler_id}][W{worker_id}] Error ({current_url}): {e}")

            self.q.task_done()

            # Politeness delay: avoid overwhelming target servers
            if self.hit_rate > 0:
                time.sleep(1.0 / self.hit_rate)

    def run(self):
        self.start_time = time.time()
        print(f"[{self.crawler_id}] Crawler started: {self.origin} ({self.num_workers} worker threads)")

        # Launch multiple worker threads — all consume from the same shared queue
        workers = []
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker, args=(i,), daemon=True)
            t.start()
            workers.append(t)

        # Wait for all workers to finish
        for t in workers:
            t.join()

        self.is_running = False
        print(f"[{self.crawler_id}] Crawler completed. Total pages crawled: {self.pages_crawled}")

    def save_words(self, words, url, origin, depth):
        """Save word frequencies to letter-indexed files (e.g., A.data, B.data)."""
        os.makedirs('data/storage', exist_ok=True)
        word_counts = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1

        for word, freq in word_counts.items():
            first_letter = word[0].upper()
            filepath = f"data/storage/{first_letter}.data"

            # Entry format matches the required triple: (relevant_url, origin_url, depth)
            entry = json.dumps({
                "word": word, "freq": freq,
                "relevant_url": url, "origin_url": origin, "depth": depth
            })

            # Use storage lock to prevent concurrent file write corruption
            with db.lock:
                with open(filepath, 'a', encoding='utf-8') as f:
                    f.write(entry + '\n')

    def stop(self):
        """Gracefully stop this crawler."""
        self.is_running = False