import json
from openai import OpenAI
from loguru import logger
from core.config import OPENAI_API_KEY, OPENAI_API_BASE, LLM_MODEL

def filter_and_extract_recommendations(tweets):
    """
    使用大模型过滤并提取A股推荐和复盘信息
    """
    if not tweets:
        logger.warning("没有传入任何推文进行分析。")
        return None
        
    if not OPENAI_API_KEY:
        logger.error("未配置 OPENAI_API_KEY，无法进行AI分析。")
        return None

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE
    )
    
    # 构造prompt
    prompt = """
    角色设定：资深A股市场分析师与研报提炼专家。
    任务目标：对输入的推文数据进行结构化分析，高度精炼A股（中国大陆股市）的复盘观点与前瞻策略。
    
    【核心过滤原则】（必须严格遵守）
    1. 合规第一：无条件剔除所有涉政、意识形态、社会事件及非金融类敏感信息。只保留纯粹的股票逻辑。
    2. 专注A股：自动忽略日常闲聊。
    
    【输出格式与要求】（极简风格）
    请以专业的金融研报风格输出Markdown，字尽其意，严禁冗长的背景铺垫或解释。
    若无有效A股信息，仅回复：“今日暂无A股高价值观点。”
    
    ### 一、 市场复盘
    - 概括大盘情绪与核心主线（限200字内）。
    
    ### 二、 核心观点与标的
    （按板块或主线分类，格式如下，剔除无逻辑的纯粹喊单，提到具体个股时请务必附上A股股票代码）
    - **[板块/主线名称]**
      - `标的(股票代码)或细分方向`：核心逻辑提取（限30字内）。(@博主名)
    
    输入数据如下（可能包含机器翻译内容，请统一输出为中文）：
    """
    
    # 限制推文数量，避免超出 LLM 上下文导致错误
    if len(tweets) > 120:
        logger.warning(f"推文数量过多 ({len(tweets)}条)，截取最新的 120 条送入分析")
        tweets = tweets[-120:]
        
    tweets_json = json.dumps(tweets, ensure_ascii=False, indent=2)
    
    logger.info(f"正在调用 {LLM_MODEL} 模型进行分析，推文数量: {len(tweets)}")
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一位资深的A股分析师，擅长用极简、专业的金融研报语言提炼市场核心观点。"},
                {"role": "user", "content": prompt + "\n" + tweets_json}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        logger.success("AI 分析完成！")
        return result
        
    except Exception as e:
        logger.error(f"调用LLM时发生错误: {e}")
        return None

if __name__ == "__main__":
    # 测试代码
    sample_tweets = [
        {"author": "fxtrader", "text": "今天A股大盘缩量震荡，半导体板块异动。明天继续关注中芯国际，逻辑是国产替代加速。", "time": "2026-04-22 15:30:00"},
        {"author": "sanhuyanxishe", "text": "BTC又破新高了，牛回速归！", "time": "2026-04-22 16:00:00"}
    ]
    res = filter_and_extract_recommendations(sample_tweets)
    print(res)
