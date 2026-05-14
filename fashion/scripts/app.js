const FashionApp = {
    currentSection: 'feed',
    currentFeedTab: 'all',
    initialized: false,

    init() {
        if (this.initialized) return;
        this.initialized = true;
        this.updateLastTime();
        this.renderStats();
        this.renderFeed();
        this.renderProducts();
        this.renderElements();
        this.renderTrends();
        this.renderAlerts();
        this.bindEvents();
    },

    updateLastTime() {
        const now = new Date();
        const timeStr = now.toLocaleString('zh-CN', { 
            year: 'numeric', 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        const el = document.getElementById('lastUpdateTime');
        if (el) el.textContent = timeStr;
    },

    renderStats() {
        const stats = MOCK_DATA.stats;
        const el1 = document.getElementById('fashionStatHitCount');
        const el2 = document.getElementById('fashionStatElementCount');
        const el3 = document.getElementById('fashionStatTrendMatch');
        const el4 = document.getElementById('fashionStatMargin');
        if (el1) el1.textContent = stats.hitCount;
        if (el2) el2.textContent = stats.elementCount;
        if (el3) el3.textContent = stats.trendMatch;
        if (el4) el4.textContent = stats.margin;
    },

    renderFeed() {
        const container = document.getElementById('fashionFeedStream');
        if (!container) return;
        const items = MOCK_DATA.feedItems;
        container.innerHTML = items.map(item => FashionRenderers.feedItem(item)).join('');
    },

    renderProducts() {
        const container = document.getElementById('fashionProductCards');
        if (!container) return;
        const products = MOCK_DATA.hitProducts;
        container.innerHTML = products.map(p => FashionRenderers.productCard(p)).join('');
    },

    renderElements() {
        const listContainer = document.getElementById('fashionElementsList');
        const suggestionsContainer = document.getElementById('fashionSuggestionsGrid');
        if (!listContainer || !suggestionsContainer) return;
        listContainer.innerHTML = MOCK_DATA.topElements.map(e => FashionRenderers.elementCard(e)).join('');
        suggestionsContainer.innerHTML = MOCK_DATA.visualSuggestions.map(s => FashionRenderers.suggestionCard(s)).join('');
    },

    renderTrends() {
        const container = document.getElementById('fashionTrendsGrid');
        if (!container) return;
        container.innerHTML = MOCK_DATA.trends.map(t => FashionRenderers.trendCard(t)).join('');
    },

    renderAlerts() {
        const container = document.getElementById('fashionAlertsList');
        if (!container) return;
        container.innerHTML = MOCK_DATA.alerts.map(a => FashionRenderers.alertCard(a)).join('');
    },

    bindEvents() {
        document.querySelectorAll('.fashion-nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });

        document.querySelectorAll('.fashion-feed-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.currentFeedTab = tab.dataset.tab;
                document.querySelectorAll('.fashion-feed-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.filterFeed();
            });
        });

        const refreshBtn = document.getElementById('fashionRefreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }

        const modalClose = document.getElementById('fashionModalClose');
        if (modalClose) {
            modalClose.addEventListener('click', () => {
                this.closeModal();
            });
        }

        const modalOverlay = document.getElementById('fashionModalOverlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeModal();
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    },

    switchSection(section) {
        this.currentSection = section;

        document.querySelectorAll('.fashion-nav-item').forEach(item => item.classList.remove('active'));
        const activeNav = document.querySelector(`.fashion-nav-item[data-section="${section}"]`);
        if (activeNav) activeNav.classList.add('active');

        const sections = ['fashionContentFeed', 'fashionProductsGrid', 'fashionElementsSection', 'fashionTrendsSection', 'fashionAlertsSection'];
        const sectionMap = {
            feed: 'fashionContentFeed',
            products: 'fashionProductsGrid',
            elements: 'fashionElementsSection',
            trends: 'fashionTrendsSection',
            alerts: 'fashionAlertsSection'
        };

        sections.forEach(s => {
            const el = document.getElementById(s);
            if (el) el.style.display = 'none';
        });

        const targetId = sectionMap[section];
        const targetEl = document.getElementById(targetId);
        if (targetEl) targetEl.style.display = 'block';

        const titles = {
            feed: '每日信息流',
            products: '爆品推荐',
            elements: '爆品元素',
            trends: '趋势追踪',
            alerts: '避坑预警'
        };

        const breadcrumbs = {
            feed: '信息流',
            products: '爆品推荐',
            elements: '爆品元素',
            trends: '趋势追踪',
            alerts: '避坑预警'
        };

        const titleEl = document.getElementById('fashionPageTitle');
        const breadcrumbEl = document.getElementById('fashionBreadcrumbCurrent');
        if (titleEl) titleEl.textContent = titles[section] || '';
        if (breadcrumbEl) breadcrumbEl.textContent = breadcrumbs[section] || '';
    },

    filterFeed() {
        const feedItems = document.querySelectorAll('.fashion-feed-item');
        feedItems.forEach(item => {
            if (this.currentFeedTab === 'all') {
                item.style.display = 'flex';
            } else if (this.currentFeedTab === 'trends') {
                item.style.display = item.dataset.type === 'trend' ? 'flex' : 'none';
            } else if (this.currentFeedTab === 'alerts') {
                item.style.display = item.dataset.type === 'alert' ? 'flex' : 'none';
            } else if (this.currentFeedTab === 'supply') {
                item.style.display = item.dataset.type === 'supply' ? 'flex' : 'none';
            }
        });
    },

    refreshData() {
        const btn = document.getElementById('fashionRefreshBtn');
        if (!btn) return;
        btn.style.opacity = '0.6';
        btn.style.pointerEvents = 'none';

        setTimeout(() => {
            this.updateLastTime();
            btn.style.opacity = '1';
            btn.style.pointerEvents = 'auto';
        }, 1200);
    },

    openProductModal(productId) {
        const product = MOCK_DATA.hitProducts.find(p => p.id === productId);
        if (!product) return;

        const modal = document.getElementById('fashionModalOverlay');
        const title = document.getElementById('fashionModalTitle');
        const body = document.getElementById('fashionModalBody');

        if (!modal || !title || !body) return;

        title.textContent = '商品详情';
        body.innerHTML = `
            <div class="fashion-modal-product-title">${product.title}</div>
            <div class="fashion-modal-product-url">${product.url}</div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">定价</div>
                <div class="fashion-modal-field-value mono">${product.price}</div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">品类</div>
                <div class="fashion-modal-field-value">${product.category}</div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">综合得分</div>
                <div class="fashion-modal-field-value mono">${product.score} / 100</div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">核心特征</div>
                <div class="fashion-modal-field-value">
                    <div class="fashion-feed-tags" style="margin-top:4px;">
                        ${product.features.map(f => `<span class="fashion-feed-tag fit">${f}</span>`).join('')}
                    </div>
                </div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">核心卖点</div>
                <div class="fashion-modal-field-value">
                    <ul style="list-style:none;padding:0;">
                        ${product.sellingPoints.map(sp => `<li style="padding:4px 0;padding-left:16px;position:relative;">
                            <span style="position:absolute;left:0;color:var(--accent-primary);">&#8226;</span>${sp}
                        </li>`).join('')}
                    </ul>
                </div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">趋势匹配元素</div>
                <div class="fashion-modal-field-value">
                    <div class="fashion-feed-tags" style="margin-top:4px;">
                        ${product.trendMatch.map(tm => `<span class="fashion-feed-tag material">${tm}</span>`).join('')}
                    </div>
                </div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">预期毛利</div>
                <div class="fashion-modal-field-value mono" style="color:${product.margin >= 30 ? 'var(--accent-success)' : 'var(--accent-danger)'};">
                    ${product.margin}% ${product.margin < 30 ? '(低毛利预警)' : ''}
                </div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">独特性系数</div>
                <div class="fashion-modal-field-value mono">${product.uniqueness.toFixed(2)}</div>
            </div>
            <div class="fashion-modal-field">
                <div class="fashion-modal-field-label">评论状态</div>
                <div class="fashion-modal-field-value">${product.reviewStatus}</div>
            </div>
        `;

        modal.classList.add('active');
    },

    closeModal() {
        const modal = document.getElementById('fashionModalOverlay');
        if (modal) modal.classList.remove('active');
    }
};

window.FashionApp = FashionApp;
