let patentData = [];
let filteredData = [];
let currentCategory = 'all';
let currentRisk = 'all';
let currentStatus = 'all';
let currentQuickFilter = null;
let currentInfringementFilter = 'all';
let screenshotZoomLevel = 1;

const apparelCategories = {
    tops: ['shirt', 'blouse', 'top', 't-shirt', 'tshirt', 'tank', 'sleeve', 'collar', 'yoke', 'bodice', 'chest', 'breast'],
    bottoms: ['pant', 'trouser', 'skirt', 'short', 'legging', 'jean', 'slack', 'bottom', 'waist'],
    dresses: ['dress', 'jumpsuit', 'romper', 'gown', 'one-piece', 'one piece'],
    outerwear: ['jacket', 'coat', 'outerwear', 'hoodie', 'parka', 'blazer', 'windbreaker', 'cape', 'cloak'],
    underwear: ['underwear', 'bra', 'panty', 'lingerie', 'intimate', 'brief', 'boxer', 'corset', 'girdle', 'pantihose', 'hosiery', 'nursing', 'breast-feeding'],
    sportswear: ['sport', 'athletic', 'fitness', 'compression', 'yoga', 'running', 'swim', 'cycling'],
    smart: ['smart', 'wearable', 'sensor', 'electronic', 'heated', 'thermal', 'monitor', 'track'],
    accessories: ['accessory', 'belt', 'scarf', 'glove', 'hat', 'cap', 'sock', 'stocking']
};

const garmentKeywords = ['garment', 'clothing', 'apparel', 'wear', 'textile', 'fabric', 'fashion', 'footwear', 'shoe', 'sneaker', 'boot', 'sandals', 'hat', 'cap', 'belt', 'glove', 'scarf', 'sock', 'underwear', 'bra', 'panty', 'lingerie', 'shirt', 'blouse', 't-shirt', 'tshirt', 'pants', 'trouser', 'skirt', 'dress', 'jacket', 'coat', 'hoodie', 'sweater', 'shorts', 'jean', 'suit', 'tie', 'uniform'];

function classifyPatent(patent) {
    const text = ((patent.title || '') + ' ' + (patent.abstract || '') + ' ' + (patent.ipc_classification || '') + ' ' + (patent.cpc_classification || '')).toLowerCase();
    const categories = [];
    for (const [cat, keywords] of Object.entries(apparelCategories)) {
        if (keywords.some(kw => text.includes(kw))) {
            categories.push(cat);
        }
    }
    return categories.length > 0 ? categories : ['other'];
}

function isGarmentRelated(patent) {
    const text = ((patent.title || '') + ' ' + (patent.abstract || '') + ' ' + (patent.ipc_classification || '') + ' ' + (patent.cpc_classification || '') + ' ' + (patent.assignee || '')).toLowerCase();
    return garmentKeywords.some(kw => text.includes(kw));
}

function getRiskLevel(patent) {
    const risk = (patent.risk_analysis?.keywords || '').toLowerCase();
    if (risk.includes('高') || risk.includes('high')) return 'high';
    if (risk.includes('中') || risk.includes('medium')) return 'medium';
    if (risk.includes('低') || risk.includes('low')) return 'low';
    return 'general';
}

function getStatus(patent) {
    const s = (patent.legal_status || '').toLowerCase();
    if (s.includes('expired') || s.includes('abandoned') || s.includes('inactive')) return 'expired';
    if (s.includes('pending')) return 'pending';
    return 'active';
}

function getScreenshotPath(patentNumber) {
    return '/output/screenshots/' + patentNumber + '_page1.png';
}

async function loadPatentData() {
    try {
        const response = await fetch('/output/patent_report_latest.json?t=' + Date.now());
        if (!response.ok) throw new Error('Failed to load');
        const data = await response.json();
        const allPatents = (data.patents || []).map(p => ({
            ...p,
            _categories: classifyPatent(p),
            _risk: getRiskLevel(p),
            _status: getStatus(p)
        }));
        patentData = allPatents;
        updateStats();
        applyFilters();
    } catch (error) {
        console.error('Error:', error);
        showEmptyState('Unable to load patent data. Please run the crawler first.');
    }
}

function updateStats() {
    document.getElementById('statTotal').textContent = patentData.length;
    document.getElementById('statActive').textContent = patentData.filter(p => p._status === 'active' || p._status === 'pending').length;
    document.getElementById('statExpired').textContent = patentData.filter(p => p._status === 'expired').length;
    document.getElementById('statUpdated').textContent = new Date().toLocaleDateString();

    document.getElementById('countAll').textContent = patentData.length;

    const catCounts = {};
    patentData.forEach(p => p._categories.forEach(c => { catCounts[c] = (catCounts[c] || 0) + 1; }));
    document.getElementById('countTops').textContent = catCounts.tops || 0;
    document.getElementById('countBottoms').textContent = catCounts.bottoms || 0;
    document.getElementById('countDresses').textContent = catCounts.dresses || 0;
    document.getElementById('countOuterwear').textContent = catCounts.outerwear || 0;
    document.getElementById('countUnderwear').textContent = catCounts.underwear || 0;
    document.getElementById('countSportswear').textContent = catCounts.sportswear || 0;
    document.getElementById('countSmart').textContent = catCounts.smart || 0;
    document.getElementById('countAccessories').textContent = catCounts.accessories || 0;

    const highCount = patentData.filter(p => p._risk === 'high').length;
    const medCount = patentData.filter(p => p._risk === 'medium').length;
    const lowCount = patentData.filter(p => p._risk === 'low').length;
    document.getElementById('countHighRisk').textContent = highCount;
    document.getElementById('countMedRisk').textContent = medCount;
    document.getElementById('countLowRisk').textContent = lowCount;
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    filteredData = patentData.filter(patent => {
        if (searchTerm) {
            const fields = [patent.patent_number, patent.title, patent.inventor, patent.assignee, patent.abstract].filter(Boolean).join(' ').toLowerCase();
            if (!fields.includes(searchTerm)) return false;
        }

        if (currentCategory !== 'all' && !patent._categories.includes(currentCategory)) return false;
        if (currentRisk !== 'all' && patent._risk !== currentRisk) return false;
        if (currentStatus !== 'all' && patent._status !== currentStatus) return false;
        
        if (currentInfringementFilter === 'active' && patent._status !== 'active' && patent._status !== 'pending') return false;
        if (currentInfringementFilter === 'high-risk' && patent._risk !== 'high') return false;
        if (currentInfringementFilter === 'medium-risk' && patent._risk !== 'medium') return false;
        
        if (currentQuickFilter) {
            const text = ((patent.title || '') + ' ' + (patent.abstract || '') + ' ' + (patent.ipc_classification || '') + ' ' + (patent.cpc_classification || '')).toLowerCase();
            if (!text.includes(currentQuickFilter)) return false;
        }

        return true;
    });

    renderGrid();
    document.getElementById('resultCount').innerHTML = `Showing <strong>${filteredData.length}</strong> of ${patentData.length} patents`;
}

function renderGrid() {
    const grid = document.getElementById('patentGrid');

    if (filteredData.length === 0) {
        grid.innerHTML = `<div class="empty-state"><div class="empty-state-title">No patents found</div><div class="empty-state-desc">Try adjusting your filters or search terms</div></div>`;
        return;
    }

    grid.innerHTML = filteredData.map((patent, idx) => {
        const screenshotUrl = getScreenshotPath(patent.patent_number);
        const statusBadge = patent._status === 'active' ? '<span class="badge badge-active">Active</span>' :
            patent._status === 'expired' ? '<span class="badge badge-expired">Expired</span>' :
            '<span class="badge badge-pending">Pending</span>';

        const riskBadge = patent._risk === 'high' ? '<span class="badge badge-risk-high">High Risk</span>' :
            patent._risk === 'medium' ? '<span class="badge badge-risk-medium">Medium Risk</span>' :
            patent._risk === 'low' ? '<span class="badge badge-risk-low">Low Risk</span>' :
            '<span class="badge badge-risk-general">General</span>';

        const categoryTags = patent._categories.map(c => `<span class="tag">${c}</span>`).join('');
        const riskLabel = patent._risk === 'high' ? 'High Risk' : patent._risk === 'medium' ? 'Medium Risk' : patent._risk === 'low' ? 'Low Risk' : 'General';

        return `
            <div class="patent-card" data-idx="${idx}" onclick="openDetail(${idx})">
                <div class="card-header">
                    <div class="card-title-area">
                        <div class="card-patent-number">${escapeHtml(patent.patent_number)}</div>
                        <div class="card-title">${highlightText(escapeHtml(patent.title))}</div>
                    </div>
                    <div class="card-badges">
                        ${statusBadge}
                        ${riskBadge}
                    </div>
                </div>
                <div class="card-screenshot">
                    <img src="${screenshotUrl}" alt="Patent screenshot" onerror="this.parentElement.innerHTML='<div class=\\'card-screenshot-placeholder\\'>No screenshot available</div>'">
                    <div class="card-screenshot-overlay"></div>
                </div>
                <div class="card-infringement-bar">
                    <div class="infringement-indicator ${patent._risk}"></div>
                    <div class="infringement-text">
                        <strong>${riskLabel}</strong> - ${patent._categories.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}
                    </div>
                </div>
                <div class="card-body">
                    <div class="card-meta">
                        <div class="meta-item">
                            <div class="meta-label">Inventor</div>
                            <div class="meta-value">${escapeHtml(patent.inventor || '-')}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Assignee</div>
                            <div class="meta-value">${escapeHtml(patent.assignee || '-')}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Publication Date</div>
                            <div class="meta-value">${escapeHtml(patent.publication_date || '-')}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Type</div>
                            <div class="meta-value">${escapeHtml(patent.type || '-')}</div>
                        </div>
                    </div>
                    <div class="card-abstract">${escapeHtml(patent.abstract || 'No abstract available')}</div>
                    <div class="card-tags">${categoryTags}</div>
                    <div class="card-actions">
                        ${patent.links?.uspto ? `<a href="${escapeHtml(patent.links.uspto)}" target="_blank" rel="noopener" class="card-action-link" onclick="event.stopPropagation()">USPTO View</a>` : ''}
                        ${patent.links?.pdf ? `<a href="${escapeHtml(patent.links.pdf)}" target="_blank" rel="noopener" class="card-action-link" onclick="event.stopPropagation()">PDF Download</a>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function openDetail(idx) {
    const patent = filteredData[idx];
    if (!patent) return;

    document.getElementById('detailPatentNumber').textContent = patent.patent_number;
    document.getElementById('detailTitle').textContent = patent.title;

    const screenshotUrl = getScreenshotPath(patent.patent_number);
    const statusLabel = patent._status === 'active' ? 'Active' : patent._status === 'expired' ? 'Expired' : 'Pending';
    const riskLabel = patent._risk === 'high' ? 'High Risk' : patent._risk === 'medium' ? 'Medium Risk' : patent._risk === 'low' ? 'Low Risk' : 'General';

    const ipcCodes = (patent.classifications?.ipc || '').split(/[,，]/).filter(Boolean).slice(0, 5);
    const cpcCodes = (patent.classifications?.cpc || '').split(/[,，]/).filter(Boolean).slice(0, 5);

    document.getElementById('detailBody').innerHTML = `
        <div class="detail-section">
            <div class="detail-section-title">Patent Document Preview</div>
            <div class="detail-screenshot" id="detailScreenshot">
                <img src="${screenshotUrl}" alt="Patent preview" id="screenshotImage" onerror="this.parentElement.innerHTML='<div style=\\'padding:2rem;text-align:center;color:var(--text-muted)\\'>No screenshot available</div>'">
                <div class="screenshot-controls">
                    <button class="screenshot-btn" onclick="zoomScreenshot(-0.2)" title="Zoom Out">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    </button>
                    <button class="screenshot-btn" onclick="resetZoom()" title="Reset Zoom">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                    </button>
                    <button class="screenshot-btn" onclick="zoomScreenshot(0.2)" title="Zoom In">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                    </button>
                    <button class="screenshot-btn" onclick="openFullscreen()" title="Fullscreen">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>
                    </button>
                </div>
            </div>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">Overview</div>
            <div class="detail-meta-grid">
                <div class="detail-meta-item">
                    <div class="meta-label">Legal Status</div>
                    <div class="meta-value">${statusLabel}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Infringement Risk</div>
                    <div class="meta-value">${riskLabel}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Inventor</div>
                    <div class="meta-value">${escapeHtml(patent.inventor || '-')}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Assignee</div>
                    <div class="meta-value">${escapeHtml(patent.assignee || '-')}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Publication Date</div>
                    <div class="meta-value">${escapeHtml(patent.publication_date || '-')}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Filing Date</div>
                    <div class="meta-value">${escapeHtml(patent.filing_date || '-')}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Patent Type</div>
                    <div class="meta-value">${escapeHtml(patent.type || '-')}</div>
                </div>
                <div class="detail-meta-item">
                    <div class="meta-label">Expiration Date</div>
                    <div class="meta-value">${escapeHtml(patent.expiration_date || '-')}</div>
                </div>
            </div>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">Abstract</div>
            <div class="detail-abstract">${escapeHtml(patent.abstract || 'No abstract available')}</div>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">IPC Classifications</div>
            <div class="detail-classifications">
                ${ipcCodes.length > 0 ? ipcCodes.map(c => `<span class="classification-tag">${escapeHtml(c.trim())}</span>`).join('') : '<span style="color:var(--text-muted);font-size:0.75rem">Not available</span>'}
            </div>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">CPC Classifications</div>
            <div class="detail-classifications">
                ${cpcCodes.length > 0 ? cpcCodes.map(c => `<span class="classification-tag">${escapeHtml(c.trim())}</span>`).join('') : '<span style="color:var(--text-muted);font-size:0.75rem">Not available</span>'}
            </div>
        </div>
    `;

    document.getElementById('detailActions').innerHTML = `
        ${patent.links?.pdf ? `<a href="${escapeHtml(patent.links.pdf)}" target="_blank" rel="noopener" class="detail-action-btn primary">Download PDF</a>` : ''}
        ${patent.links?.uspto ? `<a href="${escapeHtml(patent.links.uspto)}" target="_blank" rel="noopener" class="detail-action-btn">View on USPTO</a>` : ''}
    `;

    document.getElementById('detailPanel').classList.add('open');
    document.getElementById('overlay').classList.add('visible');
    
    screenshotZoomLevel = 1;
}

function zoomScreenshot(delta) {
    screenshotZoomLevel = Math.max(0.5, Math.min(3, screenshotZoomLevel + delta));
    const img = document.getElementById('screenshotImage');
    if (img) {
        img.style.transform = `scale(${screenshotZoomLevel})`;
        img.parentElement.classList.toggle('zoomed', screenshotZoomLevel > 1);
    }
}

function resetZoom() {
    screenshotZoomLevel = 1;
    const img = document.getElementById('screenshotImage');
    if (img) {
        img.style.transform = 'scale(1)';
        img.parentElement.classList.remove('zoomed');
    }
}

function openFullscreen() {
    const img = document.getElementById('screenshotImage');
    if (img && img.src) {
        window.open(img.src, '_blank');
    }
}

function closeDetail() {
    document.getElementById('detailPanel').classList.remove('open');
    document.getElementById('overlay').classList.remove('visible');
}

function highlightText(text) {
    const term = document.getElementById('searchInput').value.trim();
    if (!term || !text) return text;
    return text.replace(new RegExp(`(${escapeRegex(term)})`, 'gi'), '<span class="highlight">$1</span>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function showEmptyState(msg) {
    document.getElementById('patentGrid').innerHTML = `<div class="empty-state"><div class="empty-state-title">No Data</div><div class="empty-state-desc">${escapeHtml(msg)}</div></div>`;
}

document.getElementById('searchInput').addEventListener('input', debounce(applyFilters, 250));

document.getElementById('infringementFilter').addEventListener('change', function() {
    currentInfringementFilter = this.value;
    applyFilters();
});

document.querySelectorAll('.quick-filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const filter = this.dataset.filter;
        if (currentQuickFilter === filter) {
            currentQuickFilter = null;
            this.classList.remove('active');
        } else {
            document.querySelectorAll('.quick-filter-btn').forEach(b => b.classList.remove('active'));
            currentQuickFilter = filter;
            this.classList.add('active');
        }
        applyFilters();
    });
});

document.querySelectorAll('#categoryList .category-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('#categoryList .category-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
        currentCategory = this.dataset.category;
        applyFilters();
    });
});

document.querySelectorAll('#riskList .category-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('#riskList .category-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
        currentRisk = this.dataset.risk;
        applyFilters();
    });
});

document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        currentStatus = this.dataset.status;
        applyFilters();
    });
});

document.getElementById('detailClose').addEventListener('click', closeDetail);
document.getElementById('overlay').addEventListener('click', closeDetail);

document.getElementById('refreshBtn').addEventListener('click', loadPatentData);

document.getElementById('exportBtn').addEventListener('click', () => {
    const dataStr = JSON.stringify(filteredData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patent_export_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
});

function debounce(fn, wait) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
}

document.addEventListener('DOMContentLoaded', loadPatentData);
