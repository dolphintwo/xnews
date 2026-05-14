import httpx
import time
import hmac
import hashlib
import base64
import urllib.parse
from loguru import logger
from core.config import (
    DINGTALK_HOOK, DINGTALK_SECRET, ENABLE_DINGTALK,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM
)

def send_dingtalk_markdown(title: str, text: str):
    """
    发送 Markdown 消息到钉钉群
    """
    if not ENABLE_DINGTALK:
        return
        
    if not DINGTALK_HOOK:
        logger.warning("未配置 dingtalk_hook，跳过发送钉钉消息。")
        return
        
    hook_url = DINGTALK_HOOK
    if DINGTALK_SECRET:
        timestamp = str(round(time.time() * 1000))
        secret_enc = DINGTALK_SECRET.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, DINGTALK_SECRET)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        # 拼接签名参数
        if "?" in hook_url:
            hook_url += f"&timestamp={timestamp}&sign={sign}"
        else:
            hook_url += f"?timestamp={timestamp}&sign={sign}"
        
    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }
    
    try:
        response = httpx.post(hook_url, json=payload, headers=headers, timeout=10.0)
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                logger.success("成功发送 Markdown 报告到钉钉！")
            else:
                logger.error(f"发送钉钉消息失败，钉钉返回: {result}")
        else:
            logger.error(f"发送钉钉消息 HTTP 失败，状态码: {response.status_code}")
    except Exception as e:
        logger.error(f"发送钉钉消息异常: {e}")

def send_telegram_message(text: str):
    """
    发送消息到 Telegram Bot
    """
    if not ENABLE_TELEGRAM:
        return
        
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("未配置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳过发送 Telegram 消息。")
        return
        
    # Telegram API URL
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.success("成功发送报告到 Telegram！")
            else:
                logger.error(f"发送 Telegram 消息失败: {result}")
        else:
            logger.error(f"发送 Telegram 消息 HTTP 失败，状态码: {response.status_code}")
    except Exception as e:
        logger.error(f"发送 Telegram 消息异常: {e}")
