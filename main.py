import asyncio
import sys
import json
from datetime import datetime
from loguru import logger
import os

from core.scraper import scrape_all_accounts, get_latest_cache
from core.analyzer import filter_and_extract_recommendations
from core.config import CACHE_DIR, CRON_EXPRESSION
from core.notifier import send_dingtalk_markdown, send_telegram_message
from tools.check_balance import check_deepseek_balance
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

def save_report(report, file_path):
    """保存 Markdown 报告"""
    if not report:
        logger.error("报告生成失败。")
        return
        
    now = datetime.now()
    
    # 确保父目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        full_report = f"# {now.strftime('%Y-%m-%d %H:%M:%S')} X(Twitter) A股复盘与推荐\n\n" + report
        f.write(full_report)
        
    logger.success(f"报告已生成并保存至：{file_path}")
    
    # 推送到钉钉
    send_dingtalk_markdown(title=f"{now.strftime('%m-%d')} A股复盘与推荐", text=full_report)
    
    # 推送到 Telegram
    send_telegram_message(text=full_report)

def run_scraper():
    """仅执行抓取"""
    logger.info("开始执行推文抓取任务...")
    asyncio.run(scrape_all_accounts(hours_ago=24))
    logger.info("抓取任务执行完毕。")

def run_analyzer():
    """仅执行大模型分析最近一次的缓存"""
    logger.info("开始分析最近的抓取缓存...")
    latest_cache_file = get_latest_cache()
    if not latest_cache_file:
        logger.error("未找到任何缓存文件，请先进行抓取！")
        return
        
    md_file = latest_cache_file.replace(".json", ".md")
    if os.path.exists(md_file):
        logger.info(f"对应的分析报告已存在 ({md_file})，跳过 AI 分析以节省额度。")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                full_report = f.read()
            now = datetime.now()
            # 推送到钉钉
            send_dingtalk_markdown(title=f"{now.strftime('%m-%d')} A股复盘与推荐", text=full_report)
            # 推送到 Telegram
            send_telegram_message(text=full_report)
        except Exception as e:
            logger.error(f"读取或发送已有报告失败: {e}")
        return
        
    logger.info(f"读取本地缓存文件: {latest_cache_file}")
    try:
        with open(latest_cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            tweets = cache_data.get("tweets", [])
    except Exception as e:
        logger.error(f"读取缓存失败: {e}")
        return

    if not tweets:
        logger.warning("缓存文件中没有推文。分析结束。")
        return
        
    report = filter_and_extract_recommendations(tweets)
    save_report(report, md_file)

def run_all():
    """执行完整的抓取与分析流程"""
    logger.info("开始执行每日 X(Twitter) A股复盘与推荐抓取任务...")
    tweets, cache_file = asyncio.run(scrape_all_accounts(hours_ago=24))
    
    if not tweets:
        logger.warning("本次没有抓取到任何推文。任务结束。")
        check_deepseek_balance()
        return
        
    if not cache_file:
        logger.error("无法获取缓存文件路径，无法生成报告。")
        return
        
    md_file = cache_file.replace(".json", ".md")
    if os.path.exists(md_file):
        logger.info(f"对应的分析报告已存在 ({md_file})，跳过 AI 分析以节省额度。")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                full_report = f.read()
            now = datetime.now()
            # 推送到钉钉
            send_dingtalk_markdown(title=f"{now.strftime('%m-%d')} A股复盘与推荐", text=full_report)
            # 推送到 Telegram
            send_telegram_message(text=full_report)
        except Exception as e:
            logger.error(f"读取或发送已有报告失败: {e}")
        check_deepseek_balance()
        return
        
    report = filter_and_extract_recommendations(tweets)
    save_report(report, md_file)
    
    # 执行完毕后在日志中记录当前 DeepSeek 余额
    check_deepseek_balance()

def run_daemon():
    """以守护进程模式运行，使用 crontab 表达式定时执行"""
    if not CRON_EXPRESSION:
        logger.error("未配置 CRON_EXPRESSION，无法启动定时任务。")
        return
        
    logger.info(f"启动后台定时任务模式，当前 CRON 表达式: '{CRON_EXPRESSION}'")
    logger.info("程序将保持运行，并在到达指定时间时自动执行。")
    
    scheduler = BlockingScheduler()
    try:
        # 使用配置的 crontab 表达式添加定时任务
        trigger = CronTrigger.from_crontab(CRON_EXPRESSION)
        scheduler.add_job(run_all, trigger)
        
        # 启动调度器 (这将阻塞当前线程)
        scheduler.start()
    except ValueError as e:
        logger.error(f"CRON 表达式解析错误: {e}，请检查 .env 文件中的 CRON_EXPRESSION")
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已手动停止。")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "scraper":
            run_scraper()
        elif command == "analyzer":
            run_analyzer()
        elif command == "daemon":
            run_daemon()
        else:
            logger.error(f"未知的命令: {command}。支持的命令有: scraper, analyzer, daemon")
    else:
        logger.info("程序启动！即将执行完整的抓取和分析任务。")
        logger.info("如果首次运行，请确保已经执行 `python tools/login_x.py` 完成账号登录缓存。")
        run_all()

if __name__ == "__main__":
    main()
