# coin_price_broadcast
币圈行情播报
如何运行:<br>
1、创建一个钉钉机器人，创建的时候选择"加签"<br>
将钉钉机器人中的webhook token和sectoken填到脚本中<br>
2、自己想看那些币的行情就修改成哪个币


# 📈 Personal Crypto Monitor (DingTalk Alert)

一个轻量级的 Python 加密货币行情监控脚本。支持同时监控 **主流币**（通过 CoinGecko）和 **链上新币/Meme币**（通过 Binance Web3 Wallet 接口），并通过 **钉钉机器人** 发送实时价格报告。

支持 **持仓成本管理**，当币价达到成本线回本或盈利时，自动 **@提醒** 用户。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 功能亮点

* **多源数据聚合**：
    * 🏆 **主流币** (BTC, ETH, OKB...)：使用 CoinGecko API（无需 Key，对 IP 友好）。
    * 🚀 **新币/链上币** (AIAV, 币安人生...)：破解 Binance Web3 Wallet 接口（无需 API Key，支持中文搜索）。
* **盈亏监控**：支持设置每个代币的“持仓成本价”。
    * ❄️ 亏损/被套时显示雪花图标。
    * 🎉 回本/盈利时显示庆祝图标。
* **智能提醒**：
    * 钉钉 Markdown 消息推送，涨跌幅红绿颜色区分。
    * **自动 @用户**：只有当持仓盈利（当前价 >= 成本价）时，才会 @ 你的手机号，避免无效打扰。
* **防封锁设计**：避开 Binance 现货 API 的地区限制（如 451 Error），服务器位于受限地区（如美国）也能正常获取数据。

## 🛠️ 环境依赖

需要 Python 3.6+ 及 `requests` 库。

```bash
pip install requests
