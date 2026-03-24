// ============================================
// SEARCH.JS — Search & Pagination
// ============================================

const RESULTS_PER_PAGE = 10;
let allResults = [];
let currentPage = 1;

async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    const resultsArea = document.getElementById('resultsArea');

    if (!query || query.length < 2) {
        resultsArea.innerHTML = `
            <div class="no-results">
                <div class="icon">✏️</div>
                <p>Please enter at least 2 characters to search.</p>
            </div>`;
        return;
    }

    resultsArea.innerHTML = `
        <div class="no-results">
            <div class="icon"><div class="spinner" style="width:32px;height:32px;margin:0 auto;border-width:4px;"></div></div>
            <p>Searching...</p>
        </div>`;

    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        allResults = data.results || [];
        currentPage = 1;

        if (allResults.length > 0) {
            renderPage();
        } else {
            resultsArea.innerHTML = `
                <div class="no-results">
                    <div class="icon">🔍</div>
                    <p>No results found for this query.</p>
                    <p style="font-size:12px; margin-top:8px;">If the crawler is still running, try again shortly.</p>
                </div>`;
        }
    } catch (error) {
        console.error("Search error:", error);
        resultsArea.innerHTML = `
            <div class="no-results">
                <div class="icon">⚠️</div>
                <p style="color:#ef4444;">Could not reach the server.</p>
            </div>`;
    }
}

function renderPage() {
    const resultsArea = document.getElementById('resultsArea');
    const totalPages = Math.ceil(allResults.length / RESULTS_PER_PAGE);
    const start = (currentPage - 1) * RESULTS_PER_PAGE;
    const end = Math.min(start + RESULTS_PER_PAGE, allResults.length);
    const pageResults = allResults.slice(start, end);

    // Results info
    let html = `<p class="results-info">About ${allResults.length} results found · Page ${currentPage} / ${totalPages}</p>`;

    // Result cards
    pageResults.forEach((result, i) => {
        const globalIndex = start + i + 1;
        html += `
            <div class="result-item">
                <div class="result-item-inner">
                    <span class="result-index">${globalIndex}</span>
                    <div class="result-content">
                        <a href="${result.relevant_url}" target="_blank" class="result-url">${result.relevant_url}</a>
                        <div class="result-origin">↳ Origin: ${result.origin_url}</div>
                        <div class="result-stats">
                            <span class="badge badge-depth">📏 Depth: ${result.depth}</span>
                            <span class="badge badge-freq">📊 Frequency: ${result.freq}x</span>
                        </div>
                    </div>
                </div>
            </div>`;
    });

    // Pagination — only if more than one page
    if (totalPages > 1) {
        html += renderPagination(totalPages);
    }

    resultsArea.innerHTML = html;

    // Smooth scroll to results
    window.scrollTo({ top: 300, behavior: 'smooth' });
}

function renderPagination(totalPages) {
    // Build the "Craaaawler" word — repeat 'a' based on page count
    const extraAs = Math.min(totalPages, 12);
    const letters = [
        { char: 'C', cls: 'c' },
        { char: 'r', cls: 'r' },
    ];

    for (let i = 0; i < extraAs; i++) {
        letters.push({ char: 'a', cls: 'a' });
    }

    letters.push(
        { char: 'w', cls: 'w' },
        { char: 'l', cls: 'l' },
        { char: 'e', cls: 'e' },
        { char: 'r', cls: 'r' }
    );

    let crawlerWord = '<div class="crawler-word">';
    letters.forEach(l => {
        crawlerWord += `<span class="letter ${l.cls}">${l.char}</span>`;
    });
    crawlerWord += '</div>';

    // Page number buttons
    let pagination = '<div class="pagination-dots">';

    // Previous page arrow
    if (currentPage > 1) {
        pagination += `<a class="page-btn nav-arrow" onclick="goToPage(${currentPage - 1})">‹</a>`;
    }

    // Smart page number display (truncate with ... for many pages)
    const pages = getPageNumbers(currentPage, totalPages);
    pages.forEach(p => {
        if (p === '...') {
            pagination += `<span class="page-btn" style="cursor:default;border:none;background:transparent;color:var(--text-muted);">…</span>`;
        } else {
            const activeClass = p === currentPage ? 'active' : '';
            pagination += `<a class="page-btn ${activeClass}" onclick="goToPage(${p})">${p}</a>`;
        }
    });

    // Next page arrow
    if (currentPage < totalPages) {
        pagination += `<a class="page-btn nav-arrow" onclick="goToPage(${currentPage + 1})">›</a>`;
    }

    pagination += '</div>';

    return `<div class="pagination-container">${crawlerWord}${pagination}</div>`;
}

function getPageNumbers(current, total) {
    if (total <= 10) {
        return Array.from({ length: total }, (_, i) => i + 1);
    }

    const pages = [];

    // Always show first page
    pages.push(1);

    // Pages around current
    let rangeStart = Math.max(2, current - 2);
    let rangeEnd = Math.min(total - 1, current + 2);

    if (rangeStart > 2) pages.push('...');

    for (let i = rangeStart; i <= rangeEnd; i++) {
        pages.push(i);
    }

    if (rangeEnd < total - 1) pages.push('...');

    // Always show last page
    pages.push(total);

    return pages;
}

function goToPage(page) {
    currentPage = page;
    renderPage();
}