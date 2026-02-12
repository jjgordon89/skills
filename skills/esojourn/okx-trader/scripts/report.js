const fs = require('fs');
const path = require('path');
const OKXClient = require('../lib/okx-client');

function getConfig() {
    const configPath = '/root/.openclaw/workspace/okx_data/config.json';
    if (fs.existsSync(configPath)) {
        return JSON.parse(fs.readFileSync(configPath, 'utf8'));
    }
    return {
        apiKey: process.env.OKX_API_KEY,
        secretKey: process.env.OKX_SECRET_KEY,
        passphrase: process.env.OKX_PASSPHRASE,
        isSimulation: process.env.OKX_IS_SIMULATION === 'true'
    };
}

async function runReport() {
    try {
        const client = new OKXClient(getConfig());
        const [fills, pendingOrders] = await Promise.all([
            client.request('/trade/fills', 'GET', { instId: 'BTC-USDT' }),
            client.request('/trade/orders-pending', 'GET', { instId: 'BTC-USDT' })
        ]);
        
        if (fills.error || pendingOrders.error) {
            console.error('API Error:', fills.error || pendingOrders.error);
            return;
        }

        const oneHourAgo = Date.now() - (60 * 60 * 1000);
        const recentFills = Array.isArray(fills) ? fills.filter(f => parseInt(f.ts) > oneHourAgo) : [];

        const stats = {
            micro: { buyUsdt: 0, buyQty: 0, buyCount: 0, sellUsdt: 0, sellQty: 0, sellCount: 0 },
            main: { buyUsdt: 0, buyQty: 0, buyCount: 0, sellUsdt: 0, sellQty: 0, sellCount: 0 }
        };

        recentFills.forEach(f => {
            const px = parseFloat(f.fillPx || 0);
            const sz = parseFloat(f.fillSz || 0);
            const type = sz < 0.001 ? 'micro' : 'main';
            if (f.side === 'buy') {
                stats[type].buyUsdt += px * sz; stats[type].buyQty += sz; stats[type].buyCount++;
            } else {
                stats[type].sellUsdt += px * sz; stats[type].sellQty += sz; stats[type].sellCount++;
            }
        });

        const formatStats = (s) => {
            const avgB = s.buyQty > 0 ? (s.buyUsdt / s.buyQty).toFixed(2) : '0.00';
            const avgS = s.sellQty > 0 ? (s.sellUsdt / s.sellQty).toFixed(2) : '0.00';
            return `  - 成交: ${s.buyCount + s.sellCount} 笔 (买 ${s.buyCount} / 卖 ${s.sellCount})\n  - 均价: 买 ${avgB} / 卖 ${avgS}\n  - 总额: 买 ${s.buyUsdt.toFixed(2)} / 卖 ${s.sellUsdt.toFixed(2)} USDT`;
        };

        const buyOrders = Array.isArray(pendingOrders) ? pendingOrders.filter(o => o.side === 'buy').sort((a, b) => parseFloat(b.px) - parseFloat(a.px)) : [];
        const sellOrders = Array.isArray(pendingOrders) ? pendingOrders.filter(o => o.side === 'sell').sort((a, b) => parseFloat(a.px) - parseFloat(b.px)) : [];

        const now = new Date();
        const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);

        let output = `📊 **OKX 网格策略报表 (${timeStr} UTC)**\n\n`;
        output += `🌀 **小网格 (0.0003 BTC)**\n${formatStats(stats.micro)}\n\n`;
        output += `🐋 **大网格 (0.0020 BTC)**\n${formatStats(stats.main)}\n\n`;
        output += `📝 **挂单概览 (${Array.isArray(pendingOrders) ? pendingOrders.length : 0} 笔):**\n`;
        output += `📈 *卖单 (Top 3):* ${sellOrders.slice(0, 3).map(o => `${parseFloat(o.px).toFixed(0)}(${o.sz})`).join(', ')}\n`;
        output += `📉 *买单 (Top 3):* ${buyOrders.slice(0, 3).map(o => `${parseFloat(o.px).toFixed(0)}(${o.sz})`).join(', ')}\n\n`;
        output += `(注: OKX-Trader Skill 自动生成)`;

        console.log(output);
    } catch (e) {
        console.error('Error:', e.message);
    }
}

runReport();
