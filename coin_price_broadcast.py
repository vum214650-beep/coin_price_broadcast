import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
import signal
import sys
from typing import Dict, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- 配置类 (请在此处修改你的持仓) ---
class Config:
    # 1. 钉钉配置
    DINGTALK_ACCESS_TOKEN = "xxxxxx"
    DINGTALK_SECRET = "xxxxx"  # TODO: 务必替换真实密钥
    DINGTALK_KEYWORD = "alert"
    
    # 2. 你的手机号 (用于触发 @提醒)
    # 当代币价格 >= 成本价时，机器人会 @这个手机号
    MY_PHONE_NUMBER = "你的手机号"  # TODO: 替换为你的真实手机号
    
    # 轮询间隔 (秒)
    INTERVAL_SECONDS = 300 
    
    # === 数据源 1: CoinGecko (主流币) ===
    COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"
    
    # 格式: "显示名称": {"id": "API_ID", "cost": 成本价}
    # 如果只是观察，cost 填 0
    COINGECKO_TOKENS = {
        "BTC":  {"id": "bitcoin",     "cost": 65000.0},  # 比如成本是 65000
        "ETH":  {"id": "ethereum",    "cost": 3500.0},
        "BNB":  {"id": "binancecoin", "cost": 600.0},
        "OKB":  {"id": "okb",         "cost": 221.0},
        "DOGE": {"id": "dogecoin",    "cost": 0.4},        # 0 代表只观察，不计算盈亏
    }

    # === 数据源 2: Binance Web3 钱包 (链上新币) ===
    BINANCE_WALLET_API = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
    
    # 格式: "Symbol": 成本价
    BINANCE_WALLET_TOKENS = {
        "AIAV": 0.12,    # 比如成本 0.12
        "JOJO": 0.089,
        "币安人生": 0.28,    # 没买，填0
        "BAS": 0.036,
        "EDEN": 0.27,
        "SENTIS": 0.062,
        "MITO": 0.2,
        "4": 0.12,
        "ALEO": 0.33,
        "RWA": 0.2,
        "UPTOP": 0.2,
        "AIOT": 0.3,
        "AIA": 0.15
    }

# --- 网络请求工具 ---
def get_session():
    session = requests.Session()
    retry = Retry(connect=3, read=3, redirect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

session = get_session()

# --- 核心逻辑 ---

def get_coingecko_prices() -> Dict[str, dict]:
    """获取 CoinGecko 价格"""
    if not Config.COINGECKO_TOKENS:
        return {}

    # 提取所有 ID
    ids = ",".join([v["id"] for v in Config.COINGECKO_TOKENS.values()])
    params = {
        "ids": ids,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"} 
        resp = session.get(Config.COINGECKO_API, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        results = {}
        for symbol, conf in Config.COINGECKO_TOKENS.items():
            token_id = conf["id"]
            cost = conf["cost"]
            
            item = data.get(token_id, {})
            price = item.get("usd")
            change = item.get("usd_24h_change")
            
            results[symbol] = {
                "price": price, 
                "change": change, 
                "cost": cost
            }
        return results
    except Exception as e:
        logger.error(f"CoinGecko API Error: {e}")
        return {}

def get_binance_wallet_prices() -> Dict[str, dict]:
    """获取 Binance Web3 价格"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = session.get(Config.BINANCE_WALLET_API, headers=headers, timeout=10)
        resp.raise_for_status()
        json_data = resp.json()
        
        raw_list = json_data.get("data")
        if not isinstance(raw_list, list):
            return {}

        market_map = {}
        for token in raw_list:
            sym = token.get("symbol")
            if sym:
                market_map[sym] = token

        results = {}
        for symbol, cost in Config.BINANCE_WALLET_TOKENS.items():
            token_data = market_map.get(symbol)
            if token_data:
                price = token_data.get("price", 0)
                change = token_data.get("percentChange24h", 0)
                results[symbol] = {
                    "price": price, 
                    "change": change, 
                    "cost": cost
                }
        return results
    except Exception as e:
        logger.error(f"Binance Wallet API Error: {e}")
        return {}

# --- 辅助函数 ---
def format_number(val, is_percent=False):
    if val is None or val == "N/A": return "N/A"
    try:
        val = float(val)
        if is_percent:
            return f"{val:+.2f}%"
        return f"${val:.4f}" if val < 10 else f"${val:.2f}"
    except:
        return "N/A"

def get_trend_emoji(change_val):
    try:
        val = float(change_val)
        if val > 0: return "🟢"
        if val < 0: return "🔴"
        return "⚪"
    except:
        return "⚪"

def generate_line(symbol, data) -> Tuple[str, bool]:
    """
    生成单行报告，并判断是否需要 @人
    返回: (报告字符串, 是否达到成本价)
    """
    price = data.get("price")
    change = data.get("change")
    cost = data.get("cost", 0)
    
    if not price or price == "N/A":
        return "", False

    try:
        current_price_f = float(price)
        
        # 基础显示
        line = f"- {get_trend_emoji(change)} **{symbol}**: {format_number(price)} ({format_number(change, True)})"
        
        is_profit = False
        # 如果设置了成本价
        if cost and cost > 0:
            # 计算是否回本/盈利 (当前价 >= 成本价)
            if current_price_f >= cost:
                is_profit = True
                profit_icon = "🎉"  # 盈利图标
            else:
                profit_icon = "❄️"  # 亏损/被套图标
            
            # 增加成本显示
            line += f" | 💰本: {cost} {profit_icon}"
            
        return line, is_profit

    except Exception as e:
        logger.error(f"Format error for {symbol}: {e}")
        return "", False

def send_dingtalk(content: str, at_user: bool = False):
    """
    发送钉钉消息
    at_user: True 时会 @配置的手机号
    """
    timestamp = str(int(time.time() * 1000))
    secret = Config.DINGTALK_SECRET
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(secret_enc, string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    url = f"https://oapi.dingtalk.com/robot/send?access_token={Config.DINGTALK_ACCESS_TOKEN}&timestamp={timestamp}&sign={sign}"
    
    # 构建 @ 对象
    at_payload = {
        "isAtAll": False
    }
    if at_user and Config.MY_PHONE_NUMBER:
        at_payload["atMobiles"] = [Config.MY_PHONE_NUMBER]

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "持仓监控日报",
            "text": f"### 📊 持仓监控报告\n\n{content}\n\n> 🕒 {time.strftime('%H:%M:%S')}"
        },
        "at": at_payload
    }

    try:
        resp = session.post(url, json=payload, timeout=5)
        if resp.json().get("errcode") != 0:
            logger.error(f"钉钉发送失败: {resp.text}")
        else:
            logger.info(f"发送成功 (是否@人: {at_user})")
    except Exception as e:
        logger.error(f"发送异常: {e}")

def job():
    logger.info("开始抓取...")
    
    cg_data = get_coingecko_prices()
    wallet_data = get_binance_wallet_prices()
    
    report_lines = []
    should_alert_user = False  # 标记本轮是否需要 @人
    
    # 1. 处理 CoinGecko 数据
    if cg_data:
        report_lines.append("**🏆 主流持仓**")
        for sym in Config.COINGECKO_TOKENS.keys():
            if sym in cg_data:
                line, is_profit = generate_line(sym, cg_data[sym])
                if line:
                    report_lines.append(line)
                    if is_profit: should_alert_user = True
        report_lines.append("---")

    # 2. 处理 Web3 钱包数据
    if wallet_data:
        report_lines.append("**🚀 新币/链上持仓**")
        has_data = False
        for sym in Config.BINANCE_WALLET_TOKENS.keys():
            if sym in wallet_data:
                line, is_profit = generate_line(sym, wallet_data[sym])
                if line:
                    has_data = True
                    report_lines.append(line)
                    if is_profit: should_alert_user = True
        if not has_data:
             report_lines.append("*(暂无有效数据)*")

    # 3. 发送逻辑
    if len(report_lines) > 2:
        msg = "\n".join(report_lines)
        msg += f"\n\n###### Tag: {Config.DINGTALK_KEYWORD}"
        
        # 如果触发了盈利条件，消息最后加一行提示
        if should_alert_user:
            msg += f"\n\n🚨 **恭喜！有代币达到目标成本价！** @{Config.MY_PHONE_NUMBER}"
            
        send_dingtalk(msg, at_user=should_alert_user)
    else:
        logger.warning("未获取到有效数据")

# --- 启动 ---
def signal_handler(sig, frame):
    logger.info('退出程序')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    logger.info(f"成本监控已启动 | 间隔: {Config.INTERVAL_SECONDS}s")
    logger.info(f"配置手机号: {Config.MY_PHONE_NUMBER}")
    
    job()
    
    while True:
        time.sleep(Config.INTERVAL_SECONDS)
        job()
