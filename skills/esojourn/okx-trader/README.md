# OKX Trader Skill

[![ClawHub](https://img.shields.io/badge/ClawHub-okx--trader-blue)](https://clawhub.ai/esojourn/okx-trader)

Professional automated grid trading system for OKX, designed for OpenClaw.
专为 OpenClaw 设计的 OKX 专业自动化网格交易系统。

## Trading Logic / 交易逻辑

The bot implements a **Dynamic Symmetric Grid** strategy:
机器人执行**动态对称网格**策略：

1.  **Maintenance (每5分钟维护):** Every 5 minutes, the bot compares current market price against planned grid levels. If a level is missing an order, it places a new limit order.
    每5分钟，机器人对比当前市价与计划网格水位。如果某个水位缺失订单，则下达新的限价单。
2.  **Rescale (自动移动):** If the price moves beyond the `trailingPercent` threshold of the current range, the bot cancels all orders and re-centers the grid around the new price.
    如果价格超出当前区间设定的偏移阈值，机器人将取消所有订单，并以新价格为中心重置网格。
3.  **Profit Taking (止盈):** Sell orders are only placed if they meet the `minProfitGap` requirement relative to the average position cost (for Micro grid).
    （针对小网格）卖单仅在满足相对于持仓均价的最小利润间隔时才会下达。

## Configuration / 配置

Files should be placed in `/root/.openclaw/workspace/okx_data/`:
文件应存放在 `/root/.openclaw/workspace/okx_data/` 目录下：

### `config.json`
```json
{
  "apiKey": "YOUR_API_KEY",
  "secretKey": "YOUR_SECRET_KEY",
  "passphrase": "YOUR_PASSPHRASE",
  "isSimulation": true
}
```

### `grid_settings.json`
Supports `main` and `micro` configurations.
支持 `main` 和 `micro` 配置。

## Environment Variables / 环境变量

- `OKX_API_KEY`
- `OKX_SECRET_KEY`
- `OKX_PASSPHRASE`
- `OKX_IS_SIMULATION` (default: false)

## Disclaimer / 免责声明

This software is for educational purposes only. Do not trade money you cannot afford to lose.
本软件仅用于教学目的。请勿使用你无法承受损失的资金进行交易。
