import threading
import os

class Storage:
    def __init__(self, visited_file="data/visited_urls.data"):
        # Set provides O(1) lookup for visited URL checks
        self.visited_urls = set()

        # Thread lock to prevent concurrent write conflicts
        self.lock = threading.Lock()

        # File path for persisting visited URLs (enables resume after interruption)
        self.visited_file = visited_file
        self._load_visited()

    def _load_visited(self):
        """Load previously visited URLs from disk (resume support)."""
        if os.path.exists(self.visited_file):
            try:
                with open(self.visited_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            self.visited_urls.add(url)
                print(f"[Storage] Resumed: loaded {len(self.visited_urls)} previously visited URLs from disk.")
            except Exception as e:
                print(f"[Storage] Warning: could not load visited URLs file: {e}")

    def is_visited(self, url):
        """Check if a URL has already been visited."""
        with self.lock:
            return url in self.visited_urls

    def mark_visited(self, url):
        """Mark a URL as visited and persist to disk."""
        with self.lock:
            self.visited_urls.add(url)
            # Append to file for persistence (enables resume after crash)
            try:
                os.makedirs(os.path.dirname(self.visited_file), exist_ok=True)
                with open(self.visited_file, 'a', encoding='utf-8') as f:
                    f.write(url + '\n')
            except Exception as e:
                print(f"[Storage] Warning: could not persist visited URL: {e}")

    def get_visited_count(self):
        """Return the total number of URLs visited so far (for dashboard display)."""
        with self.lock:
            return len(self.visited_urls)

# Application-wide singleton storage instance
db = Storage()