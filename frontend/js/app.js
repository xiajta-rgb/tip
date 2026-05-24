let patentData = [];
let filteredData = [];
let currentCategory = 'all';
let currentAssignee = 'all';
let currentStatus = 'all';
let currentQuickFilter = null;
let currentInfringementFilter = 'all';
let screenshotZoomLevel = 1;

const garmentCategoryLabels = {
    'men': "男上装",
    'women': "女上装",
    '外套': "外套",
    '背心': "背心",
    '卫衣': "卫衣",
    '裤子': "裤子",
    '套装': "套装",
    '连衣裙': "连衣裙",
    'men-bottoms': "男裤子",
    'women-bottoms': "女裤子",
    'men-suits': "男套装",
    'women-suits': "女套装",
    'dresses': "连衣裙",
    'all': "全部",
};

const apparelCategories = {
    'men': { label: "男上装" },
    'women': { label: "女上装" },
    'men-bottoms': { label: "男裤子" },
    'women-bottoms': { label: "女裤子" },
    'men-suits': { label: "男套装" },
    'women-suits': { label: "女套装" },
    'dresses': { label: "连衣裙" },
};

const garmentTypeKeywords = {
    tops: ['shirt', 'blouse', 'top', 't-shirt', 'tshirt', 'tank', 'polo', 'henley', 'camisole', 'bodice', 'crop', 'pullover', 'sweater', 'hoodie', 'jersey', 'tunic', 'halter'],
    bottoms: ['pant', 'trouser', 'skirt', 'short', 'legging', 'jean', 'slack', 'cargo', 'chinos', 'bermuda', 'sweatpant', 'capri', 'culotte'],
    dresses: ['dress', 'jumpsuit', 'romper', 'gown', 'one-piece', 'one piece', 'frock'],
    suits: ['suit', 'set', 'ensemble', 'coordinate', ' coordi'],
    outerwear: ['jacket', 'coat', 'outerwear', 'hoodie', 'parka', 'blazer', 'windbreaker', 'cape', 'cloak', 'anorak', 'raincoat', 'overcoat', 'vest'],
    underwear: ['underwear', 'bra', 'panty', 'lingerie', 'intimate', 'brief', 'boxer', 'corset', 'girdle', 'pantihose', 'hosiery', 'slip'],
    accessories: ['accessory', 'belt', 'scarf', 'glove', 'hat', 'cap', 'sock', 'stocking', 'tie', 'bow', 'necktie']
};

const genderKeywords = {
    men: ['men', 'male', 'man', 'mens', 'boy', 'boys'],
    women: ['women', 'female', 'woman', 'womens', 'girl', 'girls', 'ladies', 'lady', 'her', 'she']
};

const garmentKeywords = ['garment', 'clothing', 'apparel', 'wear', 'textile', 'fabric', 'fashion', 'footwear', 'shoe', 'sneaker', 'boot', 'sandals', 'suit', 'uniform', 'costume', 'outfit', 'attire'];

function getTwoTags(visualCategory) {
    if (!visualCategory) return ['all'];
    
    const parts = visualCategory.split('-');
    if (parts.length >= 2) {
        const gender = parts[0];
        const type = parts.slice(1).join('-');
        
        const upperTypes = ['短袖T', '七分袖T', '长袖T', '无袖T', '背心', 'Polo衫', '卫衣', '开衫', '衬衫', '毛衣', '马甲', '外套', '滑雪服', '短袖开衫', '七分袖开衫', '长袖开衫', '宽松罩衫', '上装', '泳衣上装', '短款连衣裙', '中长连衣裙', '长款连衣裙', '连衣裙'];
        const lowerTypes = ['中裤', '长裤', '短裤', '运动裤/卫裤', '紧身裤', '抓绒紧身长裤', '非抓绒紧身长裤', '战术长裤', '软壳裤', '高尔夫长裤', '运动长裤', '雨裤', '半身裙', '短裙', '中长裙', '泳裙', '背带短裤', '背带中长裤', '背带长裤', '下装'];
        const suitTypes = ['套装', '运动套装', '休闲套装', '西装套装', '皮肤衣套装', '泳衣套装', '连体泳衣'];
        
        let firstTag;
        if (lowerTypes.includes(type)) {
            firstTag = gender === 'men' ? 'men-bottoms' : 'women-bottoms';
        } else if (suitTypes.includes(type)) {
            firstTag = gender === 'men' ? 'men-suits' : 'women-suits';
        } else if (upperTypes.includes(type) || type === '连衣裙') {
            firstTag = gender === 'men' ? 'men-tops' : 'women-tops';
        } else {
            firstTag = gender === 'men' ? 'men-tops' : 'women-tops';
        }
        
        return [firstTag, 'type-' + type];
    }
    
    return ['all'];
}

function getPdfFilename(localPath) {
    if (!localPath) return '';
    const parts = localPath.split(/[/\\]/);
    const filename = parts[parts.length - 1];
    return filename;
}

function getScreenshotFilename(localPath) {
    if (!localPath) return '';
    const parts = localPath.split(/[/\\]/);
    const filename = parts[parts.length - 1];
    return filename;
}

function cleanPatentNumber(patentNumber) {
    if (!patentNumber) return '';
    return patentNumber.replace(/^US\s*/i, '').replace(/\s+/g, '').replace(/-/g, '');
}

function classifyPatent(patent) {
    const categories = [];
    
    if (patent._visualCategory && patent._visualCategory !== 'unknown' && patent._visualCategory !== 'garment') {
        return getTwoTags(patent._visualCategory);
    }
    
    const title = (patent.title || '').toLowerCase();
    const abstract = (patent.abstract || '').toLowerCase();
    const text = title + ' ' + abstract;
    
    const isMen = genderKeywords.men.some(kw => text.includes(kw));
    const isWomen = genderKeywords.women.some(kw => text.includes(kw));
    
    for (const [type, keywords] of Object.entries(garmentTypeKeywords)) {
        if (keywords.some(kw => text.includes(kw))) {
            if (isMen && type === 'tops') { categories.push('men-tops'); break; }
            if (isWomen && type === 'tops') { categories.push('women-tops'); break; }
            if (isMen && type === 'bottoms') { categories.push('men-bottoms'); break; }
            if (isWomen && type === 'bottoms') { categories.push('women-bottoms'); break; }
            if (isMen && type === 'suits') { categories.push('men-suits'); break; }
            if (isWomen && type === 'suits') { categories.push('women-suits'); break; }
            if (isMen) categories.push('men-tops');
            else if (isWomen) categories.push('women-tops');
            else if (type === 'dresses') categories.push('dresses');
            break;
        }
    }
    
    if (categories.length === 0) {
        const hasGarment = garmentKeywords.some(kw => text.includes(kw));
        if (hasGarment) {
            if (isMen) categories.push('men-tops');
            else if (isWomen) categories.push('women-tops');
            else categories.push('all');
        }
    }
    
    return categories.length > 0 ? categories : ['all'];
}

function getRiskLevel(patent) {
    const risk = (patent.risk_level || '').toLowerCase();
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

function getScreenshotPath(patent) {
    if (patent._screenshotPath) {
        const filename = getScreenshotFilename(patent._screenshotPath);
        const fullUrl = '/output/screenshots/' + filename;
        return fullUrl;
    }
    const cleanNum = patent.patent_number_clean || cleanPatentNumber(patent.patent_number || '');
    return '/output/screenshots/' + cleanNum + '_page1.png';
}

async function loadPatentData() {
    try {
        const response = await fetch('/output/patent_report_latest.json?t=' + Date.now());
        if (!response.ok) throw new Error('Failed to load');
        const data = await response.json();
        const allPatents = (data.patents || [])
            .filter(p => {
                const abstract = (p.abstract || '').trim().toLowerCase();
                const patentType = (p.type || '').toLowerCase();
                const patentNumber = p.patent_number || '';
                const isDesignPatent = patentType.includes('design') || 
                                      patentType.includes('外观') ||
                                      patentNumber.startsWith('US D') || 
                                      patentNumber.startsWith('D');
                return isDesignPatent || (abstract && abstract !== 'no abstract available');
            })
            .map(p => {
                const jsonCategories = Array.isArray(p._categories) ? p._categories : [];
                const autoCategories = classifyPatent(p);
                const finalCategories = jsonCategories.length > 0 && jsonCategories[0] !== 'all' ? jsonCategories : autoCategories;

                const localPdfPath = (p.local_files && p.local_files.pdf_path) ? p.local_files.pdf_path : (p.pdf_path || '');
                const localScreenshotPath = (p.local_files && p.local_files.screenshot_path) ? p.local_files.screenshot_path : (p.screenshot_path || '');

                const pdfUrl = localPdfPath ? '/output/pdfs/' + getPdfFilename(localPdfPath) : '';
                const screenshotPath = localScreenshotPath ? localScreenshotPath : '';

                return {
                    ...p,
                    _categories: finalCategories,
                    _visualCategory: p._visualCategory || null,
                    _assignee: (p.assignee || 'Unknown').trim(),
                    _status: getStatus(p),
                    _pdfUrl: pdfUrl,
                    _localPdfPath: localPdfPath,
                    _screenshotPath: screenshotPath,
                    _usptoUrl: p.link || '',
                    patent_number_clean: p.patent_number_clean || cleanPatentNumber(p.patent_number || '')
                };
            });

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
    const styleCounts = {};
    patentData.forEach(p => {
        if (Array.isArray(p._categories)) {
            p._categories.forEach(c => {
                catCounts[c] = (catCounts[c] || 0) + 1;
                if (['外套', '背心', '卫衣', '裤子', '套装'].includes(c)) {
                    styleCounts[c] = (styleCounts[c] || 0) + 1;
                }
            });
        }
    });
    
    document.getElementById('countMen').textContent = catCounts['men'] || 0;
    document.getElementById('countWomen').textContent = catCounts['women'] || 0;
    document.getElementById('countMenBottoms').textContent = catCounts['men-bottoms'] || 0;
    document.getElementById('countWomenBottoms').textContent = catCounts['women-bottoms'] || 0;
    document.getElementById('countMenSuits').textContent = catCounts['men-suits'] || 0;
    document.getElementById('countWomenSuits').textContent = catCounts['women-suits'] || 0;
    document.getElementById('countDresses').textContent = catCounts['dresses'] || 0;
    
    document.getElementById('countOuterwear').textContent = styleCounts['外套'] || 0;
    document.getElementById('countVest').textContent = styleCounts['背心'] || 0;
    document.getElementById('countHoodie').textContent = styleCounts['卫衣'] || 0;
    document.getElementById('countPants').textContent = styleCounts['裤子'] || 0;
    document.getElementById('countSuits').textContent = styleCounts['套装'] || 0;

    const assigneeCounts = {};
    patentData.forEach(p => {
        const a = (p.assignee || p._assignee || 'Unknown').trim();
        if (a) assigneeCounts[a] = (assigneeCounts[a] || 0) + 1;
    });
    document.getElementById('countAllAssignees').textContent = patentData.length;
    const assigneeList = document.getElementById('assigneeList');
    const sortedAssignees = Object.entries(assigneeCounts).sort((a, b) => b[1] - a[1]);
    sortedAssignees.forEach(([name, count]) => {
        const li = document.createElement('li');
        li.className = 'category-item';
        li.dataset.assignee = name;
        li.innerHTML = `<span title="${name}">${name.length > 20 ? name.substring(0, 20) + '...' : name}</span><span class="category-count">${count}</span>`;
        assigneeList.appendChild(li);
    });
}

function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    filteredData = patentData.filter(patent => {
        if (searchTerm) {
            const fields = [patent.patent_number, patent.title, patent.inventor, patent.assignee, patent.abstract].filter(Boolean).join(' ').toLowerCase();
            const tagLabels = patent._categories.map(c => getCategoryDisplayName(c)).join(' ').toLowerCase();
            if (!fields.includes(searchTerm) && !tagLabels.includes(searchTerm)) return false;
        }

        if (currentCategory !== 'all' && !patent._categories.includes(currentCategory)) return false;
        if (currentAssignee !== 'all' && patent._assignee !== currentAssignee) return false;
        if (currentStatus !== 'all' && patent._status !== currentStatus) return false;

        return true;
    });

    renderGrid();
    document.getElementById('resultCount').innerHTML = `Showing <strong>${filteredData.length}</strong> of ${patentData.length} patents`;
}

function getCategoryDisplayName(cat) {
    if (garmentCategoryLabels[cat]) return garmentCategoryLabels[cat];
    if (apparelCategories[cat]?.label) return apparelCategories[cat].label;
    return cat;
}

function renderGrid() {
    const grid = document.getElementById('patentGrid');

    if (filteredData.length === 0) {
        grid.innerHTML = `<div class="empty-state"><div class="empty-state-title">No patents found</div><div class="empty-state-desc">Try adjusting your filters or search terms</div></div>`;
        return;
    }

    grid.innerHTML = filteredData.map((patent, idx) => {
        const screenshotUrl = getScreenshotPath(patent);
        const statusBadge = patent._status === 'active' ? '<span class="badge badge-active">Active</span>' :
            patent._status === 'expired' ? '<span class="badge badge-expired">Expired</span>' :
            '<span class="badge badge-pending">Pending</span>';

        const categoryLabels = patent._categories.map(c => getCategoryDisplayName(c));
        const categoryTags = categoryLabels.map(label => `<span class="tag">${label}</span>`).join('');

        return `
            <div class="patent-card" data-idx="${idx}" onclick="openDetail(${idx})">
                <div class="card-header">
                    <div class="card-title-area">
                        <div class="card-patent-number">${escapeHtml(patent.patent_number)}</div>
                        <div class="card-title">${highlightText(escapeHtml(patent.title))}</div>
                    </div>
                    <div class="card-badges">
                        ${statusBadge}
                    </div>
                </div>
                <div class="card-screenshot" onclick="event.stopPropagation(); openImageModal('${screenshotUrl}')">
                    <img src="${screenshotUrl}" alt="Patent screenshot" onerror="this.parentElement.innerHTML='<div class=\\'card-screenshot-placeholder\\'>No screenshot available</div>'">
                    <div class="card-screenshot-overlay"></div>
                    <div class="card-screenshot-zoom-hint">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.3-4.3"></path>
                            <path d="M11 8v6"></path>
                            <path d="M8 11h6"></path>
                        </svg>
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
                    <div class="card-tags-row">
                        ${categoryTags ? `<div class="card-tags">${categoryTags}</div>` : ''}
                        ${patent._pdfUrl ? `<button class="card-action-btn" onclick="event.stopPropagation(); openPdfModal('${escapeHtml(patent.patent_number_clean || patent.patent_number)}')">View PDF</button>` : ''}
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

    const screenshotUrl = getScreenshotPath(patent);
    const statusLabel = patent._status === 'active' ? 'Active' : patent._status === 'expired' ? 'Expired' : 'Pending';

    const ipcCodes = (patent.classifications?.ipc || '').split(/[,，]/).filter(Boolean).slice(0, 5);
    const cpcCodes = (patent.classifications?.cpc || '').split(/[,，]/).filter(Boolean).slice(0, 5);

    const categoryLabels = patent._categories.map(c => getCategoryDisplayName(c)).join(' / ');

    document.getElementById('detailBody').innerHTML = `
        <div class="detail-section">
            <div class="detail-section-title">Patent Document Preview</div>
            <div class="detail-screenshot-container">
                <img src="${screenshotUrl}" alt="Patent screenshot" class="detail-screenshot" id="detailScreenshot">
                <div class="screenshot-controls">
                    <button class="screenshot-btn" onclick="zoomScreenshot(-0.2)">-</button>
                    <button class="screenshot-btn" onclick="zoomScreenshot(0.2)">+</button>
                    <button class="screenshot-btn" onclick="resetZoom()">Reset</button>
                </div>
            </div>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">Patent Information</div>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Patent Number</div>
                    <div class="detail-value">${escapeHtml(patent.patent_number)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Title</div>
                    <div class="detail-value">${escapeHtml(patent.title)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Inventor</div>
                    <div class="detail-value">${escapeHtml(patent.inventor || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Assignee</div>
                    <div class="detail-value">${escapeHtml(patent.assignee || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Publication Date</div>
                    <div class="detail-value">${escapeHtml(patent.publication_date || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Filing Date</div>
                    <div class="detail-value">${escapeHtml(patent.filing_date || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Type</div>
                    <div class="detail-value">${escapeHtml(patent.type || '-')}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Legal Status</div>
                    <div class="detail-value">${statusLabel}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Category</div>
                    <div class="detail-value">${categoryLabels}</div>
                </div>
            </div>
        </div>
        ${patent.abstract ? `
        <div class="detail-section">
            <div class="detail-section-title">Abstract</div>
            <div class="detail-abstract">${escapeHtml(patent.abstract)}</div>
        </div>
        ` : ''}
        ${ipcCodes.length > 0 ? `
        <div class="detail-section">
            <div class="detail-section-title">IPC Classifications</div>
            <div class="detail-codes">${ipcCodes.map(c => `<span class="code-tag">${escapeHtml(c.trim())}</span>`).join('')}</div>
        </div>
        ` : ''}
        ${cpcCodes.length > 0 ? `
        <div class="detail-section">
            <div class="detail-section-title">CPC Classifications</div>
            <div class="detail-codes">${cpcCodes.map(c => `<span class="code-tag">${escapeHtml(c.trim())}</span>`).join('')}</div>
        </div>
        ` : ''}
        <div class="detail-section">
            <div class="detail-section-title">Actions</div>
            <div class="detail-actions">
                ${patent._pdfUrl ? `<button class="detail-action-btn" onclick="openPdfModal('${escapeHtml(patent.patent_number_clean || patent.patent_number)}')">View PDF</button>` : ''}
            </div>
        </div>
    `;

    document.getElementById('detailPanel').classList.add('active');
    document.body.style.overflow = 'hidden';
    screenshotZoomLevel = 1;
}

function closeDetail() {
    document.getElementById('detailPanel').classList.remove('active');
    document.body.style.overflow = '';
}

function zoomScreenshot(delta) {
    screenshotZoomLevel = Math.max(0.5, Math.min(3, screenshotZoomLevel + delta));
    const img = document.getElementById('detailScreenshot');
    if (img) {
        img.style.transform = `scale(${screenshotZoomLevel})`;
    }
}

function resetZoom() {
    screenshotZoomLevel = 1;
    const img = document.getElementById('detailScreenshot');
    if (img) {
        img.style.transform = 'scale(1)';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function highlightText(text) {
    const searchTerm = document.getElementById('searchInput').value.trim();
    if (!searchTerm) return text;
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function showEmptyState(message) {
    document.getElementById('patentGrid').innerHTML = `<div class="empty-state"><div class="empty-state-title">${message}</div></div>`;
}

let imageZoomLevel = 1;
let imagePanX = 0;
let imagePanY = 0;
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let hasDragged = false;
let dragThreshold = 5;

function openImageModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('imageModalImg');
    const content = document.getElementById('imageModalContent');
    img.src = imageUrl;
    imageZoomLevel = 1;
    imagePanX = 0;
    imagePanY = 0;
    hasDragged = false;
    img.style.transform = `scale(${imageZoomLevel}) translate(0px, 0px)`;
    modal.classList.add('visible');
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('imageModalImg');
    modal.classList.remove('visible');
    img.src = '';
    document.body.style.overflow = '';
    imageZoomLevel = 1;
    imagePanX = 0;
    imagePanY = 0;
    isDragging = false;
    hasDragged = false;
}

function updateImageTransform() {
    const img = document.getElementById('imageModalImg');
    if (img) {
        img.style.transform = `scale(${imageZoomLevel}) translate(${imagePanX}px, ${imagePanY}px)`;
    }
}

function setupImageModalInteractions() {
    const content = document.getElementById('imageModalContent');
    const img = document.getElementById('imageModalImg');
    if (!content || !img) return;

    content.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        imageZoomLevel = Math.max(0.5, Math.min(5, imageZoomLevel + delta));
        updateImageTransform();
    }, { passive: false });

    img.addEventListener('mousedown', (e) => {
        if (imageZoomLevel > 1) {
            isDragging = true;
            hasDragged = false;
            dragStartX = e.clientX - imagePanX * imageZoomLevel;
            dragStartY = e.clientY - imagePanY * imageZoomLevel;
            content.classList.add('dragging');
            e.preventDefault();
            e.stopPropagation();
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = Math.abs(e.clientX - (dragStartX + imagePanX * imageZoomLevel));
        const dy = Math.abs(e.clientY - (dragStartY + imagePanY * imageZoomLevel));
        if (dx > dragThreshold || dy > dragThreshold) {
            hasDragged = true;
        }
        imagePanX = (e.clientX - dragStartX) / imageZoomLevel;
        imagePanY = (e.clientY - dragStartY) / imageZoomLevel;
        updateImageTransform();
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            content.classList.remove('dragging');
        }
    });

    img.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        if (imageZoomLevel > 1) {
            imageZoomLevel = 1;
            imagePanX = 0;
            imagePanY = 0;
        } else {
            imageZoomLevel = 2;
        }
        updateImageTransform();
    });

    content.addEventListener('click', (e) => {
        if (e.target === content || e.target === img) {
            if (!hasDragged) {
                closeImageModal();
            }
            hasDragged = false;
        }
    });
}

function openPdfModal(patentNumber) {
    const patent = patentData.find(p => (p.patent_number_clean || p.patent_number) === patentNumber);
    const modal = document.getElementById('pdfModal');
    const iframe = document.getElementById('pdfModalIframe');
    const title = document.getElementById('pdfModalTitle');
    const downloadLink = document.getElementById('pdfModalDownload');

    let localPdfUrl = '/output/pdfs/' + patentNumber.replace(/\s+/g, '') + '.pdf';
    if (patent && patent._pdfUrl) {
        localPdfUrl = patent._pdfUrl;
    }

    title.textContent = 'PDF Document - ' + patentNumber;
    iframe.src = localPdfUrl;
    downloadLink.href = localPdfUrl;
    modal.classList.add('visible');
    document.body.style.overflow = 'hidden';
}

function closePdfModal() {
    const modal = document.getElementById('pdfModal');
    const iframe = document.getElementById('pdfModalIframe');
    modal.classList.remove('visible');
    iframe.src = '';
    document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', () => {
    loadPatentData();

    document.getElementById('searchInput').addEventListener('input', () => {
        applyFilters();
    });

    document.getElementById('categoryList').addEventListener('click', (e) => {
        const item = e.target.closest('.category-item');
        if (!item) return;
        
        document.querySelectorAll('#categoryList .category-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        currentCategory = item.dataset.category || 'all';
        applyFilters();
    });

    document.getElementById('assigneeList').addEventListener('click', (e) => {
        const item = e.target.closest('.category-item');
        if (!item) return;
        
        document.querySelectorAll('#assigneeList .category-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        currentAssignee = item.dataset.assignee || 'all';
        applyFilters();
    });

    document.getElementById('statusList').addEventListener('click', (e) => {
        const item = e.target.closest('.category-item');
        if (!item) return;
        
        document.querySelectorAll('#statusList .category-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        currentStatus = item.dataset.status || 'all';
        applyFilters();
    });

    document.getElementById('detailPanel').addEventListener('click', (e) => {
        if (e.target === document.getElementById('detailPanel')) {
            closeDetail();
        }
    });

    document.getElementById('detailClose').addEventListener('click', closeDetail);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDetail();
        }
    });

    document.getElementById('exportBtn').addEventListener('click', () => {
        const dataStr = JSON.stringify(filteredData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'patent_filtered_' + new Date().toISOString().slice(0,10) + '.json';
        a.click();
        URL.revokeObjectURL(url);
    });

    document.getElementById('refreshBtn').addEventListener('click', () => {
        location.reload();
    });

    document.getElementById('trendBtn').addEventListener('click', () => {
        window.location.href = '/frontend/trend/index.html';
    });

    document.getElementById('imageModalClose').addEventListener('click', closeImageModal);

    setupImageModalInteractions();

    document.getElementById('pdfModalClose').addEventListener('click', closePdfModal);
    document.getElementById('pdfModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('pdfModal')) {
            closePdfModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeImageModal();
            closePdfModal();
            closeDetail();
        }
    });
});
