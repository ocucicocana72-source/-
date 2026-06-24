"""定时任务服务 — 自动刷新基金数据、新闻、评论."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from services.cache import set_cached
import logging

logger = logging.getLogger("scheduler")
scheduler = BackgroundScheduler()


def refresh_news():
    """每30分钟刷新新闻缓存."""
    try:
        from services.news_scraper import fetch_all_news
        from services.news_analyzer import enrich_news_with_ai
        news = fetch_all_news(100)
        news = enrich_news_with_ai(news)
        set_cached("news_全部", news, ttl=3600)
        logger.info(f"新闻刷新完成: {len(news)} 条")
    except Exception as e:
        logger.error(f"新闻刷新失败: {e}")


def refresh_fund_rankings():
    """每日08:00刷新基金排行."""
    try:
        from services.fund_fetcher import get_fund_rank
        for ftype in ["股票型", "混合型", "债券型", "指数型", "QDII"]:
            funds = get_fund_rank(fund_type=ftype, limit=100)
            positive = [f for f in funds if (f.get("one_year_return") or 0) > 0]
            set_cached(f"fund_list_{ftype}_100", {"funds": positive, "type": ftype, "total": len(positive)}, ttl=86400)
        logger.info("基金排行刷新完成")
    except Exception as e:
        logger.error(f"基金排行刷新失败: {e}")


def refresh_market_mood():
    """每30分钟刷新市场情绪."""
    try:
        from services.news_scraper import fetch_all_news
        from services.news_analyzer import enrich_news_with_ai
        news = fetch_all_news(50)
        news = enrich_news_with_ai(news)
        positive = sum(1 for n in news if n.get("sentiment") == "利好")
        negative = sum(1 for n in news if n.get("sentiment") == "利空")
        total = len(news) or 1
        scores = [n.get("sentiment_score", 0.5) for n in news]
        avg_score = sum(scores) / len(scores) * 100 if scores else 50
        score = max(0, min(100, avg_score))
        result = {
            "score": round(score, 1),
            "label": "偏多" if score > 60 else "偏空" if score < 40 else "中性",
            "positive_ratio": round(positive / total * 100, 1),
            "negative_ratio": round(negative / total * 100, 1),
            "neutral_ratio": round((total - positive - negative) / total * 100, 1),
            "total_news": len(news),
        }
        set_cached("mood", result, ttl=3600)
        logger.info(f"市场情绪刷新: {score} ({result['label']})")
    except Exception as e:
        logger.error(f"市场情绪刷新失败: {e}")


def start_scheduler():
    """启动定时任务调度器."""
    scheduler.add_job(refresh_news, IntervalTrigger(minutes=30), id="refresh_news", replace_existing=True)
    scheduler.add_job(refresh_market_mood, IntervalTrigger(minutes=30), id="refresh_mood", replace_existing=True)
    scheduler.add_job(refresh_fund_rankings, CronTrigger(hour=8, minute=0), id="refresh_funds", replace_existing=True)
    scheduler.start()
    logger.info("定时任务已启动: 新闻/情绪每30分钟, 基金排行每日08:00")


def stop_scheduler():
    """停止调度器."""
    scheduler.shutdown()
