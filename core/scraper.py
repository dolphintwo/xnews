import asyncio
import os
import json
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from loguru import logger
from core.config import AUTH_FILE, ACCOUNTS_FILE, CACHE_DIR


def _debug_dir():
    now = datetime.now()
    dir_path = os.path.join(CACHE_DIR, "debug", now.strftime("%Y-%m-%d"), now.strftime("%H%M%S"))
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


async def _dump_page_debug(page, username: str, stage: str):
    debug_dir = _debug_dir()
    prefix = f"{username}_{stage}".replace("/", "_")
    screenshot_path = os.path.join(debug_dir, f"{prefix}.png")
    html_path = os.path.join(debug_dir, f"{prefix}.html")

    try:
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.warning(f"已保存调试截图: {screenshot_path}")
    except Exception as e:
        logger.warning(f"保存调试截图失败: {e}")

    try:
        html = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.warning(f"已保存调试页面HTML: {html_path}")
    except Exception as e:
        logger.warning(f"保存调试HTML失败: {e}")

def get_latest_cache():
    if not os.path.exists(CACHE_DIR):
        return None
        
    latest_file = None
    latest_time = 0
    
    for root, _, files in os.walk(CACHE_DIR):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                mtime = os.path.getmtime(file_path)
                if mtime > latest_time:
                    latest_time = mtime
                    latest_file = file_path
                    
    return latest_file

async def scrape_user_tweets(page, username: str, hours_ago: int = 24):
    """
    抓取指定用户最近的推文
    """
    tweets = []
    url = f"https://x.com/{username}"
    logger.info(f"正在抓取 @{username} ...")

    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status = response.status if response else "N/A"
        logger.info(f"@{username} 页面打开完成，HTTP状态: {status}，当前URL: {page.url}")

        # 先滚动一次触发懒加载，再等待节点出现
        try:
            await page.evaluate("window.scrollBy(0, 300)")
        except Exception:
            pass

        try:
            await page.wait_for_selector('article[data-testid="tweet"]', timeout=45000)
        except Exception as e:
            title = await page.title()
            logger.warning(f"@{username} 未等到推文节点: {e}")
            logger.warning(f"@{username} 页面标题: {title}，当前URL: {page.url}")
            await _dump_page_debug(page, username, "wait_tweet_timeout")
            return tweets

        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await page.wait_for_timeout(1500)

        articles = await page.query_selector_all('article[data-testid="tweet"]')
        logger.info(f"@{username} 页面共识别到 {len(articles)} 条 tweet 节点")

        cutoff_time = datetime.now() - timedelta(hours=hours_ago)

        for article in articles:
            content_elem = await article.query_selector('[data-testid="tweetText"]')
            if not content_elem:
                continue
            text = await content_elem.inner_text()

            time_elem = await article.query_selector('time')
            if not time_elem:
                continue
            time_str = await time_elem.get_attribute('datetime')

            if time_str:
                tweet_time = datetime.fromisoformat(time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                tweet_time = tweet_time + timedelta(hours=8)

                if tweet_time < cutoff_time:
                    continue
            else:
                tweet_time = datetime.now()

            tweets.append({
                "author": username,
                "text": text,
                "time": tweet_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        logger.info(f"@{username} 成功抓取 {len(tweets)} 条最近推文")
        return tweets

    except Exception as e:
        logger.error(f"抓取 @{username} 失败: {e}")
        try:
            logger.error(f"失败时页面URL: {page.url}")
            await _dump_page_debug(page, username, "exception")
        except Exception:
            pass
        return []

async def scrape_all_accounts(hours_ago: int = 24):
    latest_cache_file = get_latest_cache()
    if latest_cache_file:
        try:
            with open(latest_cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                last_scrape_time = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.now() - last_scrape_time < timedelta(hours=1):
                    logger.info(f"读取到1小时内的缓存数据 (文件: {latest_cache_file}, 抓取时间: {cache_data['timestamp']})，跳过本次网络请求。")
                    return cache_data["tweets"], latest_cache_file
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}，将重新进行抓取。")

    if not os.path.exists(AUTH_FILE):
        logger.error(f"未找到 {AUTH_FILE}，请先运行 python tools/login_x.py 登录。")
        return [], None

    if not os.path.exists(ACCOUNTS_FILE):
        logger.error(f"未找到 {ACCOUNTS_FILE}，请创建该文件并填入账号列表。")
        return [], None

    auth_size = os.path.getsize(AUTH_FILE)
    logger.info(f"检测到认证文件: {AUTH_FILE} (大小: {auth_size} bytes)")

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = [line.strip() for line in f if line.strip()]

    logger.info(f"本次计划抓取账号数: {len(accounts)}")
    all_tweets = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--lang=zh-CN',
                '--accept-lang=zh-CN,zh;q=0.9'
            ]
        )
        context = await browser.new_context(
            storage_state=AUTH_FILE,
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        page = await context.new_page()

        try:
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
            logger.info(f"登录态探测URL: {page.url}")
            if "login" in page.url:
                logger.warning("当前会话疑似未登录（跳转到 login）。跨机器复制 auth 可能已失效，建议在服务器执行 python tools/login_x.py 重新登录。")
                await _dump_page_debug(page, "auth", "login_probe")
        except Exception as e:
            logger.warning(f"登录态探测失败: {e}")

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        dir_path = os.path.join(CACHE_DIR, date_str)
        os.makedirs(dir_path, exist_ok=True)
        cache_file_path = os.path.join(dir_path, f"{hour_str}.json")

        for username in accounts:
            tweets = await scrape_user_tweets(page, username, hours_ago)
            all_tweets.extend(tweets)

            try:
                with open(cache_file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "timestamp": now.isoformat(),
                        "tweets": all_tweets
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"渐进式写入缓存失败: {e}")

            await page.wait_for_timeout(2000)

        await browser.close()

    logger.info(f"所有账号抓取完毕，最终结果已缓存至 {cache_file_path}")
    return all_tweets, cache_file_path

if __name__ == "__main__":
    tweets, cache_file = asyncio.run(scrape_all_accounts(24))
    for t in tweets:
        print(f"[{t['time']}] @{t['author']}: {t['text'][:50]}...")
