import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from playwright.async_api import async_playwright
from loguru import logger
from core.config import AUTH_FILE

async def login_and_save_auth():
    logger.info("正在启动浏览器...")
    logger.info("请在弹出的浏览器窗口中登录您的X(Twitter)账号。")
    logger.info("登录成功并且页面加载完成后，请回到这里按回车键继续。")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            # 添加一些参数防止被 Twitter 识别为自动化工具而拦截登录
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # 注入一段脚本覆盖 navigator.webdriver
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            await page.goto("https://x.com/login", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            logger.warning(f"页面加载可能未完全完成，但仍可尝试登录: {e}")
        
        # 阻塞等待用户登录
        input("👉 登录成功并看到您的主页后，请在此按下回车键...")
        
        # 保存认证状态
        await context.storage_state(path=AUTH_FILE)
        logger.success(f"认证信息已保存到 {AUTH_FILE}！")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_save_auth())
