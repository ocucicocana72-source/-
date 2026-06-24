"""新闻 AI 分析师 — 为每条新闻生成评论、总结、基金建议."""

from services.news_scraper import SECTORS                              # 板块定义

# ---- 板块对应基金建议 ----
SECTOR_FUND_MAP = {                                                    # 板块 → 推荐基金类型
    "科技": {"type": "股票型", "focus": "科技主题", "advice": "科技板块波动大，适合定投分批建仓"},
    "医药": {"type": "股票型", "focus": "医药主题", "advice": "医药属于刚需赛道，适合长期持有"},
    "新能源": {"type": "股票型", "focus": "新能源主题", "advice": "新能源政策敏感，关注政策动向"},
    "消费": {"type": "混合型", "focus": "消费主题", "advice": "消费板块防御性强，适合底仓配置"},
    "金融": {"type": "混合型", "focus": "金融地产", "advice": "金融板块估值低，适合价值投资"},
    "军工": {"type": "股票型", "focus": "军工主题", "advice": "军工受事件驱动明显，适合波段操作"},
    "基建": {"type": "混合型", "focus": "基建周期", "advice": "基建是稳增长抓手，关注政策力度"},
    "农业": {"type": "股票型", "focus": "农业主题", "advice": "农业受周期和天气影响大，注意风险"},
    "港股": {"type": "QDII", "focus": "港股QDII", "advice": "港股受海外流动性影响大，注意汇率风险"},
    "债券": {"type": "债券型", "focus": "债券基金", "advice": "债基适合稳健配置，利率下行时表现好"},
    "综合": {"type": "混合型", "focus": "均衡配置", "advice": "综合类新闻，建议均衡配置各类基金"},
}


def generate_comment(title: str, content: str, sentiment: str, sector: str) -> dict:
    """根据新闻内容生成 AI 评论和基金建议."""
    summary = content[:100] + "..." if len(content) > 100 else content  # 截取摘要
    if not summary:                                                    # 无内容
        summary = title                                                # 用标题作摘要

    sector_info = SECTOR_FUND_MAP.get(sector, SECTOR_FUND_MAP["综合"])  # 板块信息

    if sentiment == "利好":                                            # 利好消息
        comment = f"该消息对{sector}板块形成利好支撑。"                  # 基础评论
        if "涨" in title or "新高" in title:                           # 涨幅相关
            comment += f"{sector}板块近期表现强势，市场资金关注度提升。"
        elif "政策" in title or "利好" in title:                       # 政策利好
            comment += f"政策面持续发力，{sector}板块有望受益。"
        elif "增长" in title or "盈利" in title:                       # 增长相关
            comment += f"基本面改善信号明确，{sector}板块估值有支撑。"
        else:                                                          # 其他利好
            comment += f"建议关注{sector}板块相关基金的配置机会。"
    elif sentiment == "利空":                                          # 利空消息
        comment = f"该消息对{sector}板块构成短期压力。"                  # 基础评论
        if "跌" in title or "暴跌" in title:                           # 下跌相关
            comment += f"{sector}板块调整压力较大，注意控制仓位。"
        elif "减持" in title or "清仓" in title:                       # 减持相关
            comment += f"资金流出信号明显，短期需谨慎。"
        elif "亏损" in title or "爆雷" in title:                       # 爆雷相关
            comment += f"风险事件需重点关注，避免踩雷。"
        else:                                                          # 其他利空
            comment += f"建议观望{sector}板块，等待企稳信号。"
    else:                                                              # 中性消息
        comment = f"该消息对{sector}板块影响中性，建议持续关注动态。"

    risk_note = f"⚠️ {sector}板块短期承压，注意止损" if sentiment == "利空" else "投资有风险，入市需谨慎"  # 风险提示
    fund_advice = f"📌 {sector_info['advice']}，可关注{sector_info['focus']}类基金"  # 基金建议

    return {
        "summary": summary, "comment": comment,
        "fund_advice": fund_advice, "risk_note": risk_note,
        "recommended_type": sector_info["type"],
    }


def enrich_news_with_ai(news_list: list[dict]) -> list[dict]:
    """为新闻列表批量添加 AI 分析."""
    for item in news_list:                                             # 遍历新闻
        ai = generate_comment(                                         # 生成 AI 评论
            item.get("title", ""), item.get("content", ""),
            item.get("sentiment", "中性"), item.get("sector", "综合"),
        )
        item["ai_summary"] = ai["summary"]                            # 添加摘要
        item["ai_comment"] = ai["comment"]                            # 添加评论
        item["ai_fund_advice"] = ai["fund_advice"]                    # 添加基金建议
        item["ai_risk_note"] = ai["risk_note"]                        # 添加风险提示
        item["ai_recommended_type"] = ai["recommended_type"]          # 添加推荐类型
    return news_list                                                   # 返回结果
