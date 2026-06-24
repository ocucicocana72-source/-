"""多源财经新闻 — AKShare 多板块爬取 + 板块分类 + 情感分析 + 日期过滤."""

import akshare as ak                                                   # AKShare 金融数据
import httpx                                                           # HTTP 客户端
from bs4 import BeautifulSoup                                         # HTML 解析
from datetime import datetime, timedelta                              # 时间处理
import random                                                         # 随机打乱
from snownlp import SnowNLP                                           # 中文情感分析

# ---- 基金板块定义 ----
SECTORS = {                                                            # 板块关键词映射
    "科技": ["科技", "半导体", "芯片", "人工智能", "AI", "计算机", "软件", "数字经济", "5G", "通信"],
    "医药": ["医药", "医疗", "生物", "创新药", "中药", "疫苗", "CXO", "器械"],
    "新能源": ["新能源", "光伏", "风电", "储能", "锂电", "电池", "碳中和", "氢能"],
    "消费": ["消费", "白酒", "食品", "饮料", "家电", "零售", "免税", "餐饮"],
    "金融": ["金融", "银行", "券商", "保险", "证券", "地产", "房地产"],
    "军工": ["军工", "国防", "航天", "航空", "船舶", "兵器"],
    "基建": ["基建", "建筑", "建材", "水泥", "钢铁", "交运"],
    "农业": ["农业", "养殖", "种植", "猪肉", "鸡肉", "粮食"],
    "港股": ["港股", "恒生", "中概", "QDII", "纳斯达克", "标普"],
    "债券": ["债券", "债基", "利率", "可转债", "信用债", "国债"],
}

SEARCH_KEYWORDS = [                                                    # 多关键词搜索列表
    "基金", "医药基金", "新能源基金", "科技基金", "消费基金",
    "军工基金", "债券基金", "港股基金", "农业基金", "金融基金",
]


def filter_recent(news_list: list[dict], days: int = 7) -> list[dict]:
    """只保留最近 N 天内的新闻."""
    cutoff = datetime.now() - timedelta(days=days)                     # 计算截止时间
    result = []                                                        # 结果列表
    for item in news_list:                                             # 遍历新闻
        time_str = item.get("time", "")                                # 获取时间字符串
        try:                                                           # 解析时间
            news_time = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")  # 解析格式
        except (ValueError, IndexError):                               # 解析失败
            try:                                                       # 尝试另一种格式
                news_time = datetime.strptime(time_str[:10], "%Y-%m-%d")  # 只有日期
            except (ValueError, IndexError):                           # 仍然失败
                news_time = datetime.now()                             # 默认为当前时间
        if news_time >= cutoff:                                        # 在时间范围内
            result.append(item)                                        # 添加到结果
    return result                                                      # 返回过滤结果


def classify_sector(title: str, content: str = "") -> str:
    """根据标题和内容关键词判断所属板块."""
    text = title + " " + content                                       # 拼接文本
    scores = {}                                                        # 板块匹配分数
    for sector, keywords in SECTORS.items():                           # 遍历板块
        score = sum(1 for kw in keywords if kw in text)                # 统计匹配关键词数
        if score > 0:                                                  # 有匹配
            scores[sector] = score                                     # 记录分数
    if not scores:                                                     # 无匹配
        return "综合"                                                  # 归为综合
    return max(scores, key=scores.get)                                 # 返回最高分板块


def fetch_akshare_news(keyword: str = "基金", limit: int = 10) -> list[dict]:
    """通过 AKShare 获取东方财富新闻."""
    try:
        df = ak.stock_news_em(symbol=keyword)                          # 调用新闻接口
        results = []                                                   # 结果列表
        for _, row in df.head(limit).iterrows():                       # 遍历前N条
            title = str(row.get("新闻标题", ""))                        # 标题
            content = str(row.get("新闻内容", ""))[:300]                # 内容摘要
            results.append({                                           # 组装新闻
                "title": title,                                        # 标题
                "content": content,                                    # 内容
                "url": str(row.get("新闻链接", "")),                    # 链接
                "source": str(row.get("文章来源", "东方财富")),          # 来源
                "time": str(row.get("发布时间", "")),                   # 发布时间
                "sector": classify_sector(title, content),             # 板块分类
            })
        return results                                                 # 返回结果
    except Exception:                                                  # 接口异常
        return []                                                      # 返回空


def fetch_sina_news(limit: int = 20) -> list[dict]:
    """新浪财经新闻爬虫."""
    url = "https://finance.sina.com.cn/roll/index.d.html?cid=56588&page=1"  # 新浪滚动新闻
    try:
        resp = httpx.get(url, headers={                                # 发请求
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")                 # 解析 HTML
        links = soup.select("a[href*='finance.sina']")                 # 取新闻链接
        results = []
        for link in links:
            title = link.get_text(strip=True)                          # 提取标题
            href = link.get("href", "")                                # 提取链接
            if title and len(title) > 8:                               # 过滤无效项
                results.append({                                       # 组装结果
                    "title": title,                                    # 标题
                    "content": "",                                     # 内容（爬虫无摘要）
                    "url": href,                                       # 链接
                    "source": "新浪财经",                               # 来源
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),  # 当前时间
                    "sector": classify_sector(title),                  # 板块分类
                })
        return results[:limit]                                         # 截取
    except Exception:                                                  # 请求失败
        return []                                                      # 返回空


def fetch_tonghuashun_news(limit: int = 15) -> list[dict]:
    """同花顺财经新闻爬虫."""
    url = "https://news.10jqka.com.cn/today_list/"                    # 同花顺今日要闻
    try:
        resp = httpx.get(url, headers={                                # 发请求
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")                 # 解析 HTML
        items = soup.select("li a[href*='10jqka']")                    # 取新闻链接
        results = []
        for item in items:
            title = item.get_text(strip=True)                          # 提取标题
            href = item.get("href", "")                                # 提取链接
            if title and len(title) > 8 and href.startswith("http"):   # 过滤
                results.append({                                       # 组装结果
                    "title": title,                                    # 标题
                    "content": "",                                     # 内容
                    "url": href,                                       # 链接
                    "source": "同花顺",                                 # 来源
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),  # 当前时间
                    "sector": classify_sector(title),                  # 板块分类
                })
        return results[:limit]                                         # 截取
    except Exception:                                                  # 请求失败
        return []                                                      # 返回空


def analyze_sentiment(text: str) -> dict:
    """SnowNLP + 金融关键词修正情感分析."""
    if not text:                                                       # 空文本
        return {"label": "中性", "score": 0.5}                         # 默认中性
    positive_words = ["涨", "利好", "上涨", "新高", "突破", "反弹", "牛市", "增持", "加仓", "看好", "增长", "盈利", "分红"]  # 利好词
    negative_words = ["跌", "利空", "下跌", "暴跌", "跳水", "破位", "熊市", "减持", "清仓", "亏损", "爆雷", "退市", "违约"]  # 利空词
    pos_count = sum(1 for w in positive_words if w in text)            # 利好计数
    neg_count = sum(1 for w in negative_words if w in text)            # 利空计数
    s = SnowNLP(text)                                                  # SnowNLP 分析
    raw_score = s.sentiments                                           # 原始分数
    if pos_count > neg_count and pos_count >= 2:                       # 多利好词
        score = max(raw_score, 0.75)                                   # 上调
    elif neg_count > pos_count and neg_count >= 2:                     # 多利空词
        score = min(raw_score, 0.25)                                   # 下调
    elif pos_count > 0 and neg_count == 0:                             # 仅利好
        score = max(raw_score, 0.65)                                   # 轻微上调
    elif neg_count > 0 and pos_count == 0:                             # 仅利空
        score = min(raw_score, 0.35)                                   # 轻微下调
    else:                                                              # 无明确关键词
        score = raw_score                                              # 原始分数
    label = "利好" if score >= 0.6 else "利空" if score <= 0.4 else "中性"  # 标签
    return {"label": label, "score": round(score, 3)}                  # 返回结果


def enrich_news_with_sentiment(news_list: list[dict]) -> list[dict]:
    """批量添加情感分析."""
    for item in news_list:                                             # 遍历新闻
        text = item.get("title", "") + " " + item.get("content", "")  # 拼接文本
        sentiment = analyze_sentiment(text)                            # 分析情感
        item["sentiment"] = sentiment["label"]                        # 添加标签
        item["sentiment_score"] = sentiment["score"]                  # 添加分数
    return news_list                                                   # 返回结果


def deduplicate(news_list: list[dict]) -> list[dict]:
    """按标题去重."""
    seen = set()                                                       # 已见标题集合
    result = []                                                        # 去重结果
    for item in news_list:                                             # 遍历新闻
        title = item.get("title", "")                                  # 获取标题
        if title and title not in seen:                                # 未见过
            seen.add(title)                                            # 标记已见
            result.append(item)                                        # 添加到结果
    return result                                                      # 返回去重结果


def fetch_all_news(limit: int = 100) -> list[dict]:
    """聚合多源多板块新闻，大量内容 + 板块分类 + 情感分析."""
    all_news = []                                                      # 汇总列表

    # 1. 东方财富：多关键词搜索（每个关键词10条 × 10个 = 100条）
    for kw in SEARCH_KEYWORDS:                                         # 遍历关键词
        all_news.extend(fetch_akshare_news(kw, 10))                    # 搜索并添加

    # 2. 新浪财经
    all_news.extend(fetch_sina_news(20))                               # 添加新浪

    # 3. 同花顺
    all_news.extend(fetch_tonghuashun_news(15))                        # 添加同花顺

    # 4. 去重 + 过滤近7天 + 打乱 + 情感分析
    all_news = deduplicate(all_news)                                   # 去重
    all_news = filter_recent(all_news, days=7)                         # 只保留近7天新闻
    random.shuffle(all_news)                                           # 打乱顺序
    result = all_news[:limit]                                          # 截取指定数量
    return enrich_news_with_sentiment(result)                          # 添加情感分析后返回


def fetch_sector_news(sector: str, limit: int = 30) -> list[dict]:
    """获取指定板块的新闻."""
    all_news = fetch_all_news(200)                                     # 获取大量新闻
    if sector == "全部":                                               # 全部板块
        return all_news[:limit]                                        # 返回指定数量
    filtered = [n for n in all_news if n.get("sector") == sector]     # 按板块过滤
    return filtered[:limit]                                            # 返回指定数量
