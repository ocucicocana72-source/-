"""新闻 API 路由 — 多板块 + 板块筛选 + 搜索 + AI 分析 + 缓存."""

from fastapi import APIRouter, Query                                    # 路由和查询参数
from services.news_scraper import fetch_all_news, fetch_sector_news, SECTORS  # 新闻爬虫 + 板块定义
from services.news_analyzer import enrich_news_with_ai                  # AI 分析
from services.cache import get_cached, set_cached                      # 缓存服务

router = APIRouter()                                                   # 创建路由实例


@router.get("/sectors")                                                # 板块列表
async def get_sectors():                                               # 无需参数
    """返回所有板块名称，供前端导航使用."""                               # 接口说明
    return {                                                           # 返回板块列表
        "sectors": ["全部"] + list(SECTORS.keys()),                    # 板块名称列表
        "total": len(SECTORS) + 1,                                     # 板块总数
    }


@router.get("/")                                                       # 新闻列表
async def get_news(
    limit: int = Query(50, description="返回数量"),                     # 数量限制
    sector: str = Query("全部", description="板块筛选"),                 # 板块筛选
    sentiment: str = Query(None, description="情感筛选：利好/利空/中性"),  # 情感筛选
    search: str = Query(None, description="关键词搜索"),                 # 关键词搜索
):
    cache_key = f"news_{sector}"                                       # 缓存键
    cached = get_cached(cache_key, ttl_seconds=1800)                   # 30分钟缓存

    if cached:                                                         # 有缓存
        news = cached                                                  # 使用缓存
    else:                                                              # 无缓存
        if sector and sector != "全部":                                 # 指定板块
            news = fetch_sector_news(sector, limit)                    # 获取板块新闻
        else:                                                          # 全部板块
            news = fetch_all_news(limit)                               # 获取全部新闻
        news = enrich_news_with_ai(news)                               # 添加 AI 分析
        set_cached(cache_key, news)                                    # 存入缓存

    # 筛选
    if sentiment and sentiment in ["利好", "利空", "中性"]:             # 情感筛选
        news = [n for n in news if n.get("sentiment") == sentiment]    # 按情感过滤
    if search:                                                         # 关键词搜索
        search_lower = search.lower()                                  # 转小写
        news = [n for n in news if search_lower in n.get("title", "").lower() or search_lower in n.get("content", "").lower()]  # 模糊匹配

    return {                                                           # 返回结果
        "news": news[:limit],                                          # 新闻列表
        "total": len(news),                                            # 总数
        "sector": sector,                                              # 当前板块
        "sectors": ["全部"] + list(SECTORS.keys()),                    # 可用板块
    }


@router.get("/market-mood")                                            # 市场情绪
async def get_market_mood():                                           # 无需参数
    cached = get_cached("mood", ttl_seconds=3600)                      # 1小时缓存
    if cached:                                                         # 有缓存
        return cached                                                  # 直接返回

    news = fetch_all_news(50)                                          # 取50条新闻
    news = enrich_news_with_ai(news)                                   # 添加 AI 分析

    positive = sum(1 for n in news if n.get("sentiment") == "利好")    # 利好计数
    negative = sum(1 for n in news if n.get("sentiment") == "利空")    # 利空计数
    neutral = len(news) - positive - negative                          # 中性计数
    total = len(news) or 1                                             # 避免除零

    scores = [n.get("sentiment_score", 0.5) for n in news]             # 情感分数
    avg_score = sum(scores) / len(scores) * 100 if scores else 50      # 平均分
    score = max(0, min(100, avg_score))                                # 钳制

    # 板块热度统计
    sector_counts = {}                                                 # 板块计数
    for n in news:                                                     # 遍历新闻
        s = n.get("sector", "综合")                                    # 获取板块
        sector_counts[s] = sector_counts.get(s, 0) + 1                 # 计数
    hot_sectors = sorted(sector_counts.items(), key=lambda x: -x[1])[:5]  # 取前5热门板块

    result = {
        "score": round(score, 1),
        "label": "偏多" if score > 60 else "偏空" if score < 40 else "中性",
        "positive_ratio": round(positive / total * 100, 1),
        "negative_ratio": round(negative / total * 100, 1),
        "neutral_ratio": round(neutral / total * 100, 1),
        "total_news": len(news),
        "hot_sectors": [{"name": s, "count": c} for s, c in hot_sectors],  # 热门板块
    }
    set_cached("mood", result)                                         # 存入缓存
    return result                                                      # 返回结果
