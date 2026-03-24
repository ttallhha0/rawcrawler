from flask import Flask, request, jsonify, send_from_directory
import time
import threading
import os

# Import our custom modules
from utils.storage import db
from services.crawler_service import CrawlerJob
from services.search_service import SearchService

# Initialize Flask app. Frontend files are served from the 'demo' directory.
app = Flask(__name__, static_folder='demo')
search_service = SearchService()

# Dictionary to track active crawler threads
active_crawlers = {}

@app.route('/')
def index():
    # Serve the main crawler page as the homepage
    return send_from_directory('demo', 'crawler.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serve CSS, JS, and other static files from the demo directory
    return send_from_directory('demo', path)

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """Start a new crawler job with the parameters provided from the UI."""
    data = request.json
    origin = data.get('origin')
    max_depth = int(data.get('depth', 2))
    hit_rate = float(data.get('hit_rate', 5.0))
    max_queue_capacity = int(data.get('max_queue_capacity', 1000))
    num_workers = int(data.get('num_workers', 4))

    if not origin:
        return jsonify({"error": "Origin URL is required."}), 400

    # Crawler ID format: EpochTime_ThreadID
    epoch_time = int(time.time())
    thread_id = threading.get_ident()
    crawler_id = f"{epoch_time}_{thread_id}"

    # Create and start the crawler thread
    crawler = CrawlerJob(
        crawler_id=crawler_id,
        origin=origin,
        max_depth=max_depth,
        hit_rate=hit_rate,
        max_queue_capacity=max_queue_capacity,
        num_workers=num_workers
    )

    # Launch in background and add to tracking dictionary
    crawler.start()
    active_crawlers[crawler_id] = crawler

    return jsonify({
        "crawler_id": crawler_id,
        "status": "Active",
        "message": "Crawler started successfully in the background."
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Return current system health and per-crawler status for the dashboard."""
    # Count how many crawlers are actively running
    active_count = sum(1 for c in active_crawlers.values() if c.is_running)

    # Build per-crawler status list
    crawlers_list = []
    for cid, crawler in active_crawlers.items():
        crawlers_list.append(crawler.get_status())

    return jsonify({
        "visited_urls_count": db.get_visited_count(),
        "active_crawlers_count": active_count,
        "status": "Running" if active_count > 0 else "Idle",
        "crawlers": crawlers_list
    })

@app.route('/api/search', methods=['GET'])
def search():
    """Search indexed pages using the SearchService."""
    query = request.args.get('query', '')
    results = search_service.search(query)
    return jsonify({"results": results})

if __name__ == '__main__':
    print("Starting server... (http://localhost:5050)")
    # Ensure data directories exist
    os.makedirs('data/storage', exist_ok=True)
    os.makedirs('demo', exist_ok=True)

    # Run with threaded=True to handle concurrent requests
    app.run(debug=True, threaded=True, use_reloader=False, port=5050)