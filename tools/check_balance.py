import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from loguru import logger
from core.config import OPENAI_API_KEY

def check_deepseek_balance():
    """
    查询 DeepSeek 账号余额
    """
    if not OPENAI_API_KEY:
        logger.error("未配置 OPENAI_API_KEY，无法查询余额。")
        return None
        
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("is_available"):
                balance_infos = data.get("balance_infos", [])
                if balance_infos:
                    # 获取CNY余额信息
                    cny_info = next((info for info in balance_infos if info.get("currency") == "CNY"), None)
                    if cny_info:
                        total_balance = cny_info.get("total_balance", "0.00")
                        logger.info(f"DeepSeek 账户当前总余额: {total_balance} CNY")
                        return total_balance
                logger.warning("未找到余额数据。")
            else:
                logger.warning("DeepSeek 账号不可用。")
        else:
            logger.error(f"查询余额 HTTP 失败，状态码: {response.status_code}")
    except Exception as e:
        logger.error(f"查询余额异常: {e}")
        
    return None

if __name__ == "__main__":
    check_deepseek_balance()
