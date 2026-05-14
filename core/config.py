import os
from dotenv import load_dotenv

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 绝对路径配置
ACCOUNTS_FILE = os.path.join(ROOT_DIR, "account.txt")
AUTH_FILE = os.path.join(ROOT_DIR, "twitter_auth.json")
CACHE_DIR = os.path.join(ROOT_DIR, "caches")
DINGTALK_HOOK = os.getenv("dingtalk_hook", "")
DINGTALK_SECRET = os.getenv("dingtalk_secret", "")
ENABLE_DINGTALK = os.getenv("ENABLE_DINGTALK", "true").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"
CRON_EXPRESSION = os.getenv("CRON_EXPRESSION", "0 9,21 * * *")
