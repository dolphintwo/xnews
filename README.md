# XNews - A股推文复盘与推荐自动化分析工具

XNews 是一个自动化的信息监控与投研工具。它能够自动抓取指定 X (Twitter) 博主发布的最新推文，利用 DeepSeek (或其他 OpenAI 兼容大模型) 提炼出关于**A股（中国大陆股市）**的高价值复盘观点和个股推荐，并最终生成极简风格的 Markdown 研报，推送到您的钉钉群或 Telegram 中。

## ✨ 核心特性

- **自动化抓取**：基于 Playwright 模拟真人操作，自动绕过基本反爬虫机制，抓取最新推文。
- **智能过滤与提炼**：利用大语言模型（默认 DeepSeek），严格过滤涉政、无关闲聊及其他市场的噪音，提炼出极其精简的金融研报。
- **灵活的推送通道**：支持推送到钉钉机器人和 Telegram Bot，可自由开关。
- **无人值守守护进程**：支持自定义 Cron 表达式，挂在后台即可实现每日定时自动运行（例如每天早 9 点、晚 8 点）。
- **工具箱**：内置扫码登录、独立推送测试、大模型余额查询等辅助脚本。

---

## 📂 项目结构

```text
xnews/
├── main.py              # 项目主入口 (提供抓取、分析、守护进程等命令行模式)
├── core/                # 核心业务逻辑
│   ├── config.py        # 环境与路径配置
│   ├── scraper.py       # Playwright 推文抓取模块
│   ├── analyzer.py      # 大模型 Prompt 与分析提炼模块
│   └── notifier.py      # 钉钉 / Telegram 消息推送模块
├── tools/               # 独立工具箱
│   ├── check_balance.py # DeepSeek 余额查询
│   ├── login_x.py       # X (Twitter) 扫码登录与 Cookie 保存
│   └── test_notify.py   # 单独测试 Markdown 报告推送
├── caches/              # 自动生成的推文 JSON 数据与 Markdown 报告存放目录
├── account.txt          # 需要监听抓取的 X 博主列表（每行一个用户名）
├── .env                 # 环境变量配置文件（需手动创建）
├── .env.example         # 环境变量配置模板
└── requirements.txt     # Python 依赖清单
```

---

## 🚀 快速开始

### 1. 环境准备

确保您的系统中已安装 Python 3.9+，并安装所需依赖：

```bash
# 安装依赖库
pip install -r requirements.txt

# 安装 Playwright 所需的浏览器环境
playwright install chromium
```

### 2. 配置文件说明

1. 复制环境变量模板文件：
   ```bash
   cp .env.example .env
   ```
2. 编辑 `.env` 文件，填入您的真实信息：
   - **大模型配置**：`OPENAI_API_KEY`（如使用 DeepSeek，填入 DeepSeek API Key）。
   - **定时任务**：`CRON_EXPRESSION`（遵循标准 crontab 格式，如 `0 9,20 * * *`）。
   - **推送配置**：选择性开启 `ENABLE_DINGTALK` 或 `ENABLE_TELEGRAM`，并填入相应的 Webhook 和 Token 密钥。

3. 编辑 `account.txt`，填入您需要监控的 X (Twitter) 博主用户名，每行一个。例如：
   ```text
   elonmusk
   some_stock_analyst
   ```

### 3. 初始化登录 (首次运行必须)

为了让程序能够成功抓取推文，您需要先登录您的 X 账号并保存会话缓存：

```bash
python tools/login_x.py
```
运行后会弹出一个浏览器窗口，请在其中手动登录您的 X 账号。登录成功并看到主页后，回到终端按下 **回车键**。程序会将您的登录凭证保存在根目录的 `twitter_auth.json` 中。

---

## 🛠️ 使用方法

### 主程序命令 (`main.py`)

- **执行完整流程（抓取 + 分析 + 推送）一次并退出**：
  ```bash
  python main.py
  ```

- **仅执行推文抓取（保存 JSON 到 caches 目录）**：
  ```bash
  python main.py scraper
  ```

- **仅执行最新缓存数据的 AI 分析与推送**：
  ```bash
  python main.py analyzer
  ```

- **挂起守护进程，按 Cron 定时任务全自动运行**：
  ```bash
  python main.py daemon
  ```
  *(注：如果需要在服务器后台长期运行，推荐使用 `nohup python main.py daemon > run.log 2>&1 &`)*

### 辅助工具 (`tools/`)

- **单独查询大模型账户余额**：
  ```bash
  python tools/check_balance.py
  ```

- **测试报告推送 (无需消耗大模型额度，直接推送本地 Markdown)**：
  ```bash
  python tools/test_notify.py caches/YYYY-MM-DD/HH.md
  ```

---

## 📝 过滤与提炼原则说明

本项目内置的 Prompt 专门为 **A股市场** 优化。在 `core/analyzer.py` 中，AI 被赋予了严格的纪律：
1. **合规第一**：无条件剔除所有涉政、意识形态、社会事件及非金融类敏感信息。
2. **专注A股**：自动忽略美股、港股、加密货币及日常闲聊。
3. **极简排版**：强制字数限制，以金融研报的无序列表格式输出，自动附带A股股票代码。

您可以根据自己的需求随时调整 `core/analyzer.py` 中的系统提示词。