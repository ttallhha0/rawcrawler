document.getElementById('crawlerForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const submitButton = document.getElementById('submitBtn');
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner"></span> Starting...';

    const payload = {
        origin: document.getElementById('origin').value,
        depth: parseInt(document.getElementById('depth').value),
        hit_rate: parseFloat(document.getElementById('hit_rate').value),
        max_queue_capacity: parseInt(document.getElementById('max_queue').value),
        num_workers: parseInt(document.getElementById('num_workers').value)
    };

    try {
        const response = await fetch('/api/crawl', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        const resultDiv = document.getElementById('result');

        if (response.ok) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h3>✔ Crawler Started!</h3>
                    <p><strong>ID:</strong> ${data.crawler_id}</p>
                    <p>${data.message}</p>
                    <p style="margin-top:8px;"><a href="/status.html" style="color:var(--accent-green);">📊 Go to Dashboard →</a></p>
                </div>`;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-error">
                    <h3>✖ Error</h3>
                    <p>${data.error || 'An unknown error occurred.'}</p>
                </div>`;
        }
    } catch (error) {
        console.error("Request error:", error);
        document.getElementById('result').innerHTML = `
            <div class="alert alert-error">
                <h3>✖ Connection Error</h3>
                <p>Could not reach the server. Make sure python3 app.py is running in the terminal.</p>
            </div>`;
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '🚀 Launch Crawler in Background';
    }
});