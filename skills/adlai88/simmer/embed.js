/**
 * Simmer Embeddable Widget
 *
 * Usage:
 * <div data-simmer-market="MARKET_ID"></div>
 * <script src="https://simmer.markets/embed.js" async></script>
 *
 * Options (data attributes):
 * - data-simmer-market: Market ID (required)
 * - data-simmer-theme: "dark" | "light" (default: auto-detect)
 */

(function() {
  'use strict';

  // Allow override for local testing
  const API_BASE = window.SIMMER_API_BASE || 'https://api.simmer.markets/api';
  const REFRESH_INTERVAL = 60000; // 60 seconds

  // Inject styles once
  function injectStyles() {
    if (document.getElementById('simmer-embed-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'simmer-embed-styles';
    styles.textContent = `
      .simmer-widget {
        font-family: 'SF Mono', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 4px;
        padding: 16px;
        max-width: 400px;
        min-width: 280px;
        color: #e5e5e5;
        box-sizing: border-box;
      }
      .simmer-widget.simmer-light {
        background: #fafafa;
        border-color: #e5e5e5;
        color: #171717;
      }
      .simmer-widget-label {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #737373;
        margin-bottom: 6px;
      }
      .simmer-widget-question {
        font-size: 13px;
        line-height: 1.4;
        margin-bottom: 12px;
        font-weight: 500;
      }
      .simmer-widget-probability {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }
      .simmer-widget-pct {
        font-size: 28px;
        font-weight: 700;
        color: #34d399;
        min-width: 70px;
      }
      .simmer-widget.simmer-light .simmer-widget-pct {
        color: #059669;
      }
      .simmer-widget-bar-container {
        flex: 1;
        height: 8px;
        background: #262626;
        border-radius: 4px;
        overflow: hidden;
      }
      .simmer-widget.simmer-light .simmer-widget-bar-container {
        background: #e5e5e5;
      }
      .simmer-widget-bar {
        height: 100%;
        background: linear-gradient(90deg, #34d399, #10b981);
        border-radius: 4px;
        transition: width 0.5s ease;
      }
      .simmer-widget-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 10px;
        color: #737373;
      }
      .simmer-widget-link {
        color: #34d399;
        text-decoration: none;
        font-weight: 500;
      }
      .simmer-widget-link:hover {
        text-decoration: underline;
      }
      .simmer-widget.simmer-light .simmer-widget-link {
        color: #059669;
      }
      .simmer-widget-badge {
        opacity: 0.7;
      }
      .simmer-widget-loading {
        text-align: center;
        padding: 20px;
        color: #737373;
      }
      .simmer-widget-error {
        text-align: center;
        padding: 20px;
        color: #ef4444;
        font-size: 12px;
      }
      .simmer-widget-status {
        display: inline-block;
        font-size: 9px;
        padding: 2px 6px;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-left: 8px;
      }
      .simmer-widget-status.resolved {
        background: #1e3a5f;
        color: #60a5fa;
      }
      .simmer-widget.simmer-light .simmer-widget-status.resolved {
        background: #dbeafe;
        color: #2563eb;
      }
    `;
    document.head.appendChild(styles);
  }

  // Detect theme preference
  function detectTheme(element) {
    const explicit = element.dataset.simmerTheme;
    if (explicit === 'light' || explicit === 'dark') return explicit;

    // Auto-detect from parent background or system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  }

  // Format relative time
  function formatRelativeTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }

  // Render widget
  function renderWidget(container, data, theme) {
    const probability = Math.round(data.current_probability * 100);
    const isResolved = data.status === 'resolved';

    container.innerHTML = `
      <div class="simmer-widget ${theme === 'light' ? 'simmer-light' : ''}">
        <div class="simmer-widget-label">Simmer AI says</div>
        <div class="simmer-widget-question">
          ${escapeHtml(data.question)}
          ${isResolved ? '<span class="simmer-widget-status resolved">Resolved</span>' : ''}
        </div>
        <div class="simmer-widget-probability">
          <div class="simmer-widget-pct">${probability}%</div>
          <div class="simmer-widget-bar-container">
            <div class="simmer-widget-bar" style="width: ${probability}%"></div>
          </div>
        </div>
        <div class="simmer-widget-footer">
          <span class="simmer-widget-updated">Updated ${formatRelativeTime(data.last_updated)}</span>
          <a href="${data.embed_url}" target="_blank" rel="noopener" class="simmer-widget-link">
            View on Simmer →
          </a>
        </div>
      </div>
    `;
  }

  // Render loading state
  function renderLoading(container) {
    container.innerHTML = `
      <div class="simmer-widget">
        <div class="simmer-widget-loading">Loading prediction...</div>
      </div>
    `;
  }

  // Render error state
  function renderError(container, message) {
    container.innerHTML = `
      <div class="simmer-widget">
        <div class="simmer-widget-error">${escapeHtml(message)}</div>
      </div>
    `;
  }

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Fetch market data
  async function fetchMarketData(marketId) {
    const response = await fetch(`${API_BASE}/markets/${marketId}/embed`);
    if (!response.ok) {
      throw new Error('Market not found');
    }
    return response.json();
  }

  // Initialize a single widget
  async function initWidget(container) {
    const marketId = container.dataset.simmerMarket;
    if (!marketId) return;

    const theme = detectTheme(container);
    renderLoading(container);

    try {
      const data = await fetchMarketData(marketId);
      renderWidget(container, data, theme);

      // Set up auto-refresh (only for active markets)
      if (data.status === 'active') {
        setInterval(async () => {
          try {
            const freshData = await fetchMarketData(marketId);
            renderWidget(container, freshData, theme);
          } catch {
            // Silent fail on refresh - keep showing last data
          }
        }, REFRESH_INTERVAL);
      }
    } catch {
      renderError(container, 'Failed to load market');
    }
  }

  // Initialize all widgets on page
  function initAllWidgets() {
    injectStyles();
    const widgets = document.querySelectorAll('[data-simmer-market]');
    widgets.forEach(initWidget);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllWidgets);
  } else {
    initAllWidgets();
  }

  // Expose for manual initialization
  window.SimmerEmbed = { init: initAllWidgets, initWidget };
})();
