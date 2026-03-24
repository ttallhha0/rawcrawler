// Polls /api/status every 2 seconds and updates the dashboard
function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update active crawler count
            document.getElementById('active-crawlers').innerText = data.active_crawlers_count;

            // Update visited URL count
            document.getElementById('visited-urls').innerText = data.visited_urls_count;

            // Update system status indicator
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('sys-status');
            const statusValue = document.getElementById('sys-status-value');

            if (data.status === 'Running') {
                statusDot.className = 'status-dot running';
                statusText.textContent = `${data.active_crawlers_count} crawler(s) actively running`;
                statusValue.textContent = 'Active';
            } else {
                statusDot.className = 'status-dot idle';
                statusText.textContent = 'System is idle';
                statusValue.textContent = 'Idle';
            }

            // Render per-crawler detail cards
            renderCrawlerDetails(data.crawlers || []);
        })
        .catch(error => {
            console.error('Error updating status:', error);
        });
}

function renderCrawlerDetails(crawlers) {
    const container = document.getElementById('crawler-details');

    if (crawlers.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <div class="icon">🕷️</div>
                <p>No crawlers have been started yet.</p>
                <p style="font-size:12px; margin-top:8px;"><a href="/crawler.html" style="color:var(--accent-blue);">Start a new crawl →</a></p>
            </div>`;
        return;
    }

    let html = '<h2 style="color:var(--text-primary);margin-bottom:16px;font-size:18px;">Crawler Jobs</h2>';

    crawlers.forEach(c => {
        const statusClass = c.is_running ? 'running' : 'idle';
        const statusLabel = c.is_running ? '🟢 Running' : '⚪ Completed';
        const queuePercent = c.queue_capacity > 0 ? Math.round((c.queue_size / c.queue_capacity) * 100) : 0;
        const backPressureWarning = c.back_pressure_drops > 0
            ? `<span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;">⚠ ${c.back_pressure_drops} dropped</span>`
            : `<span class="badge" style="background:rgba(0,245,160,0.1);color:var(--accent-green);">✓ No drops</span>`;

        html += `
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <div>
                        <span class="status-dot ${statusClass}" style="vertical-align:middle;"></span>
                        <strong style="font-size:14px;">${statusLabel}</strong>
                        <span style="color:var(--text-muted);font-size:12px;margin-left:8px;">ID: ${c.crawler_id}</span>
                    </div>
                    <span style="color:var(--text-muted);font-size:12px;">⏱ ${c.elapsed_seconds}s</span>
                </div>
                <div style="color:var(--accent-blue);font-size:13px;word-break:break-all;margin-bottom:12px;">
                    🌐 ${c.origin} &nbsp;·&nbsp; Depth: ${c.max_depth} &nbsp;·&nbsp; Workers: ${c.num_workers} &nbsp;·&nbsp; Rate: ${c.hit_rate}/s
                </div>
                <div style="display:flex;gap:12px;flex-wrap:wrap;">
                    <span class="badge badge-freq">📄 ${c.pages_crawled} pages</span>
                    <span class="badge badge-depth">📦 Queue: ${c.queue_size}/${c.queue_capacity} (${queuePercent}%)</span>
                    ${backPressureWarning}
                    ${c.errors > 0 ? `<span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;">❌ ${c.errors} errors</span>` : ''}
                </div>
            </div>`;
    });

    container.innerHTML = html;
}

// Run immediately on load, then poll every 2 seconds
updateStatus();
setInterval(updateStatus, 2000);
