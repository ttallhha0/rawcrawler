import os
import json
import re

class SearchService:
    def __init__(self, storage_dir="data/storage"):
        self.storage_dir = storage_dir

    def search(self, query):
        """
        Search indexed pages for relevance to the query string.
        
        Supports multi-word queries: each word is searched in its corresponding
        letter-indexed file, and results are merged by URL with combined frequency scores.
        
        Returns a list of triples: (relevant_url, origin_url, depth) sorted by relevance.
        """
        if not query or len(query.strip()) < 2:
            return []

        # Split query into individual words, lowercase, filter short words
        words = re.findall(r'[a-z]{2,}', query.strip().lower())
        if not words:
            return []

        # Aggregate results across all query words
        # Key: (relevant_url, origin_url, depth) → total frequency
        url_scores = {}

        for word in words:
            first_letter = word[0].upper()
            filepath = os.path.join(self.storage_dir, f"{first_letter}.data")

            if not os.path.exists(filepath):
                continue

            # Read file line-by-line to avoid loading entire file into memory
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            # Match exact word
                            if data.get("word") == word:
                                key = (data["relevant_url"], data["origin_url"], data["depth"])
                                freq = data.get("freq", 0)
                                url_scores[key] = url_scores.get(key, 0) + freq
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"[Search] Error reading {filepath}: {e}")

        # Sort by total frequency score (highest relevance first)
        sorted_results = sorted(url_scores.items(), key=lambda x: x[1], reverse=True)

        # Format output as the required triples with frequency info
        formatted_results = []
        for (relevant_url, origin_url, depth), total_freq in sorted_results:
            formatted_results.append({
                "relevant_url": relevant_url,
                "origin_url": origin_url,
                "depth": depth,
                "freq": total_freq
            })

        return formatted_results