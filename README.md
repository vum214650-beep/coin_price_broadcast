
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
```

## ✨ 告警如图

![image](https://github.com/vum214650-beep/coin_price_broadcast/blob/main/73D1B0E6-785E-4BE0-9C43-7594035C5DB0.png)<br>

🚀 快速开始
克隆仓库

Bash

git clone [https://github.com/your-username/crypto-monitor-dingtalk.git](https://github.com/your-username/crypto-monitor-dingtalk.git)
cd crypto-monitor-dingtalk
配置脚本 打开脚本文件 monitor.py (假设你保存为此名)，找到 Config 类进行修改：

Python

class Config:
    # 1. 钉钉机器人设置
    DINGTALK_ACCESS_TOKEN = "你的Access Token"
    DINGTALK_SECRET = "你的SEC开头的密钥"
    MY_PHONE_NUMBER = "13800000000"  # 盈利时要@的手机号

    # 2. 设置持仓 (id参考CoinGecko URL, cost为0代表只观察)
    COINGECKO_TOKENS = {
        "BTC":  {"id": "bitcoin",     "cost": 65000.0},
        "OKB":  {"id": "okb",         "cost": 45.0},
    }

    # 3. 设置新币/链上币 (名称需与Binance Web3显示一致)
    BINANCE_WALLET_TOKENS = {
        "AIAV": 0.12,    # 成本价 0.12
        "币安人生": 0,    # 0 代表只观察
    }
运行测试

Bash

python3 monitor.py
⚙️ 后台长期运行
推荐使用 Systemd 或 Nohup 让脚本在服务器后台持续运行。

方法 A: Nohup (最简单)
Bash

nohup python3 -u monitor.py > monitor.log 2>&1 &
查看日志： tail -f monitor.log 停止脚本： pkill -f monitor.py

方法 B: Systemd (推荐，开机自启)
创建服务文件：nano /etc/systemd/system/crypto_monitor.service

写入以下内容（修改路径）：

Ini, TOML

[Unit]
Description=Crypto Monitor Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/path/to/script
ExecStart=/usr/bin/python3 -u monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
启动服务：

Bash

systemctl enable crypto_monitor
systemctl start crypto_monitor
📸 效果截图
(此处可以放一张你在钉钉收到消息的截图)

示例消息：

🏆 主流持仓

🟢 BTC: $68,000 (+2.5%) | 💰本: 65000 🎉

🔴 OKB: $42.00 (-1.2%) | 💰本: 45.0 ❄️

🚀 新币/链上持仓

🟢 AIAV: $0.13 (+15.2%) | 💰本: 0.12 🎉

🚨 恭喜！有代币达到目标成本价！ @138xxxx

⚠️ 免责声明
本工具仅供学习和个人监控使用，不构成任何投资建议。API 数据来源于公开网络，不保证 100% 的准确性和实时性。

📄 License
MIT License


---

### 💡 几个小建议：

1.  **文件重命名**：建议把脚本名字从 `test_alert.py` 改为更正式的 `monitor.py` 或 `main.py`。
2.  **隐藏密钥**：如果你真的上传到 GitHub，**千万不要**把你的 `DINGTALK_TOKEN` 和 `SECRET` 直接写在代码里上传！
    * **做法**：在代码里把那两行改成空字符串 `""`，或者写成 `os.getenv("DINGTALK_TOKEN")`，并在 README 里告诉用户需要自己填进去。
3.  **截图**：在 README 里放一张钉钉手机端的截图（记得把敏感金额打码），会极大增加别人的使用欲望。
