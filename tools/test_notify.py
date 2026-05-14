import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger
from core.notifier import send_dingtalk_markdown, send_telegram_message
from core.config import ENABLE_DINGTALK, ENABLE_TELEGRAM

def test_notify(file_path):
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    now = datetime.now()
    title = f"{now.strftime('%m-%d')} A股复盘与推荐 (测试推送)"
    
    logger.info(f"读取文件成功，字数: {len(content)}")
    
    if ENABLE_DINGTALK:
        logger.info("正在推送到钉钉...")
        send_dingtalk_markdown(title=title, text=content)
    else:
        logger.info("钉钉推送已在配置中关闭。")
        
    if ENABLE_TELEGRAM:
        logger.info("正在推送到 Telegram...")
        send_telegram_message(text=content)
    else:
        logger.info("Telegram推送已在配置中关闭。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_notify.py <markdown文件路径>")
        print("示例: python test_notify.py caches/2026-04-28/16.md")
    else:
        test_notify(sys.argv[1])
