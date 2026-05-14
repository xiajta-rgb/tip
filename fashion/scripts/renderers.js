const FashionRenderers = {
    feedItem(item) {
        return `
            <div class="fashion-feed-item" data-type="${item.type}">
                <div class="fashion-feed-icon ${item.icon}">
                    ${this.feedIconSVG(item.icon)}
                </div>
                <div class="fashion-feed-content">
                    <div class="fashion-feed-title">
                        ${item.title}
                        <span class="fashion-source-tag">${item.sourceTag}</span>
                    </div>
                    <p class="fashion-feed-desc">${item.desc}</p>
                    <div class="fashion-feed-meta">
                        <span>${item.meta}</span>
                        <span>${item.time}</span>
                    </div>
                    ${item.tags ? `<div class="fashion-feed-tags">${item.tags.map(t => `<span class="fashion-feed-tag ${t.type}">${t.text}</span>`).join('')}</div>` : ''}
                </div>
            </div>
        `;
    },

    feedIconSVG(type) {
        const icons = {
            hit: '<svg viewBox="0 0 24 24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            trend: '<svg viewBox="0 0 24 24" fill="none"><path d="M3 17l6-6 4 4 8-10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 5h4v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            alert: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 2l10 18H2L12 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="12" cy="17" r="0.5" fill="currentColor"/></svg>',
            supply: '<svg viewBox="0 0 24 24" fill="none"><rect x="2" y="7" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="14" y="7" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/><path d="M10 11h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M6 17v3M18 17v3M6 20h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
        };
        return icons[type] || icons.hit;
    },

    productCard(product) {
        const scoreClass = product.score >= 80 ? 'high' : 'potential';
        const marginClass = product.margin >= 30 ? 'good' : 'low';
        return `
            <div class="fashion-product-card" data-id="${product.id}" onclick="FashionApp.openProductModal(${product.id})">
                <div class="fashion-product-card-header">
                    <div class="fashion-product-score ${scoreClass}">${product.score}</div>
                    <div class="fashion-product-card-info">
                        <div class="fashion-product-card-title">${product.title}</div>
                        <div class="fashion-product-card-category">${product.category}</div>
                    </div>
                </div>
                <div class="fashion-product-card-body">
                    <div class="fashion-product-card-price">${product.price}</div>
                    <div class="fashion-product-card-features">
                        ${product.features.map(f => `<span class="fashion-feed-tag fit">${f}</span>`).join('')}
                    </div>
                </div>
                <div class="fashion-product-card-footer">
                    <span class="fashion-product-card-margin ${marginClass}">毛利: ${product.margin}%</span>
                    <span class="fashion-product-card-uniqueness">独特性: ${product.uniqueness.toFixed(2)}</span>
                    <div style="display:flex;gap:4px;">
                        ${product.warning ? `<span class="fashion-product-card-warning">${product.warning}</span>` : ''}
                        ${product.reviewStatus === '无有效评论' ? '<span class="fashion-product-card-review">无有效评论</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    },

    elementCard(element) {
        const rankClass = element.rank <= 3 ? 'top3' : '';
        return `
            <div class="fashion-element-card">
                <div class="fashion-element-rank ${rankClass}">#${element.rank}</div>
                <div class="fashion-element-name">${element.name}</div>
                <div class="fashion-element-standard">${element.standard}</div>
                <p class="fashion-element-desc">${element.desc}</p>
                <div class="fashion-element-meta">
                    <span>频次: <span class="fashion-element-freq">${element.freq}</span></span>
                    <span>来源: ${element.source}</span>
                </div>
            </div>
        `;
    },

    suggestionCard(suggestion) {
        return `
            <div class="fashion-suggestion-card">
                <h4>${suggestion.category}: ${suggestion.title}</h4>
                <p>${suggestion.desc}</p>
            </div>
        `;
    },

    trendCard(trend) {
        return `
            <div class="fashion-trend-card">
                <div class="fashion-trend-header">
                    <span class="fashion-trend-source">${trend.source}</span>
                    <span class="fashion-trend-heat ${trend.heat}">${trend.heat === 'high' ? '高热度' : '中热度'}</span>
                </div>
                <div class="fashion-trend-title">${trend.title}</div>
                <p class="fashion-trend-desc">${trend.desc}</p>
                <div class="fashion-trend-tags">
                    ${trend.tags.map(t => `<span class="fashion-feed-tag ${t.type}">${t.text}</span>`).join('')}
                </div>
            </div>
        `;
    },

    alertCard(alert) {
        const severityClass = alert.severity === 'critical' ? 'critical' : '';
        return `
            <div class="fashion-alert-card ${severityClass}">
                <div class="fashion-alert-icon">
                    ${alert.severity === 'critical' 
                        ? '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/><path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
                        : '<svg viewBox="0 0 24 24" fill="none"><path d="M12 2l10 18H2L12 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
                    }
                </div>
                <div class="fashion-alert-content">
                    <div class="fashion-alert-title">${alert.title}</div>
                    <p class="fashion-alert-desc">${alert.desc}</p>
                    <div class="fashion-alert-footer">
                        <span>来源: ${alert.source}</span>
                        <span>痛点: ${alert.painPoints.join(' | ')}</span>
                    </div>
                </div>
            </div>
        `;
    }
};
