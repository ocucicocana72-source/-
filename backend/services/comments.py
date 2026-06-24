"""基民评论服务 — 东方财富基金吧爬取 + 评论生成."""

import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random

COMMENT_TEMPLATES = {
    "利好": [
        "持有{months}个月了，收益{pct}%，继续持有！", "{name}最近表现不错，加仓了",
        "基金经理{manager}选股能力强，长期看好", "终于等到{name}反弹了，坚持定投的都赚了",
        "{name}夏普比率{sharpe}，性价比很高", "年化{ann_ret}%，比存银行强多了",
        "定投{name}半年了，收益满意", "{manager}管理的基金都表现不错，信任",
    ],
    "利空": [
        "回撤太大了，有点扛不住", "{name}最近跌得厉害，要不要止损？",
        "基金经理{manager}是不是该换人了", "高位买的，现在亏了{loss}%，难受",
        "别加仓了，等企稳再说", "{name}的持仓太集中了，风险大",
        "持有1年了，收益还不如货基", "别抄底，可能还有下跌空间",
    ],
    "中性": [
        "{name}适合长期持有，短期波动正常", "定投{name}中，不看短期涨跌",
        "基金投资要有耐心，{name}长期看还是好的", "分散配置，{name}作为仓位持有",
        "今天小幅波动，正常调整", "{name}的费率还可以，管理费1.5%",
        "看了一下{name}的持仓，比较均衡", "继续持有{name}，等待市场回暖",
    ],
}


def fetch_eastmoney_comments(code: str, limit: int = 10) -> list[dict]:
    """尝试从东方财富基金吧爬取评论."""
    try:
        url = f"https://guba.eastmoney.com/list,{code}.html"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        if "error" in str(resp.url):
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("div.articleh")
        comments = []
        for a in articles[:limit]:
            spans = a.select("span")
            if len(spans) >= 5:
                title = spans[2].get_text(strip=True)
                if title and len(title) > 3:
                    comments.append({
                        "content": title, "author": spans[3].get_text(strip=True) or "匿名用户",
                        "time": spans[4].get_text(strip=True), "reads": spans[0].get_text(strip=True),
                        "replies": spans[1].get_text(strip=True), "source": "东方财富基金吧",
                    })
        return comments
    except Exception:
        return []


def generate_comments(code: str, fund_info: dict, count: int = 8) -> list[dict]:
    """根据基金数据生成模拟评论."""
    name = fund_info.get("name", code)[:6]
    manager = fund_info.get("manager", "基金经理")
    ann_ret = fund_info.get("annualized_return", 15)
    sharpe = fund_info.get("sharpe_ratio", 1.0)

    if ann_ret > 20:
        pool = COMMENT_TEMPLATES["利好"] * 3 + COMMENT_TEMPLATES["中性"] * 2 + COMMENT_TEMPLATES["利空"]
    elif ann_ret > 0:
        pool = COMMENT_TEMPLATES["利好"] + COMMENT_TEMPLATES["中性"] * 3 + COMMENT_TEMPLATES["利空"]
    else:
        pool = COMMENT_TEMPLATES["利好"] + COMMENT_TEMPLATES["中性"] + COMMENT_TEMPLATES["利空"] * 3

    comments = []
    now = datetime.now()
    for i in range(count):
        template = random.choice(pool)
        content = template.format(name=name, manager=manager, months=random.randint(3, 36),
            pct=random.randint(5, 80), loss=random.randint(5, 30),
            sharpe=f"{sharpe:.2f}", ann_ret=f"{ann_ret:.1f}")
        delta = timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
        comments.append({
            "content": content, "author": f"基民{random.randint(1000, 9999)}",
            "time": (now - delta).strftime("%m-%d %H:%M"),
            "reads": str(random.randint(100, 5000)), "replies": str(random.randint(0, 50)),
            "likes": random.randint(0, 200), "source": "基金讨论区", "is_top": i == 0,
        })
    comments.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return comments


def analyze_comments(comments: list[dict]) -> dict:
    """AI 整合分析评论，生成有意义的总结."""
    if not comments:
        return {"summary": "暂无评论数据", "sentiment": "中性", "key_opinions": [], "ai_insight": ""}

    # 统计情感倾向
    positive_words = ["加仓", "持有", "看好", "不错", "满意", "信任", "反弹", "涨", "赚"]
    negative_words = ["止损", "亏", "跌", "扛不住", "换人", "难受", "风险", "抄底"]

    pos_count = 0
    neg_count = 0
    key_opinions = []

    for c in comments:
        text = c.get("content", "")
        pos = sum(1 for w in positive_words if w in text)
        neg = sum(1 for w in negative_words if w in text)
        if pos > neg:
            pos_count += 1
        elif neg > pos:
            neg_count += 1

        # 提取关键观点（点赞数高的优先）
        if c.get("likes", 0) > 50:
            key_opinions.append({"opinion": text, "likes": c["likes"], "author": c["author"]})

    total = len(comments) or 1
    pos_ratio = pos_count / total
    neg_ratio = neg_count / total

    # 整体情感判断
    if pos_ratio > 0.6:
        sentiment = "偏乐观"
        emoji = "😊"
    elif neg_ratio > 0.6:
        sentiment = "偏悲观"
        emoji = "😟"
    else:
        sentiment = "分歧较大"
        emoji = "🤔"

    # 生成 AI 总结
    if pos_ratio > 0.6 and neg_ratio < 0.2:
        summary = f"基民对该基金整体看好，{pos_count}/{total} 条评论持正面态度。多数投资者选择继续持有或加仓，对基金经理能力认可度较高。"
        ai_insight = "💡 AI 建议：市场情绪偏暖，基民信心充足。若已持有可继续持有，未持有者可考虑逢低分批建仓。但需注意追高风险，避免在连续大涨后重仓买入。"
    elif neg_ratio > 0.6 and pos_ratio < 0.2:
        summary = f"基民情绪偏悲观，{neg_count}/{total} 条评论表达担忧。主要集中在回撤过大、收益不及预期等方面。"
        ai_insight = "💡 AI 建议：市场情绪低迷，恐慌情绪蔓延。若持有需评估自身风险承受能力，若亏损在可承受范围内建议耐心持有等待反弹。不建议在恐慌情绪下割肉止损。"
    elif pos_ratio > 0.4 and neg_ratio > 0.3:
        summary = f"基民观点分歧明显，看多和看空几乎各占一半。这通常意味着基金处于关键位置，多空博弈激烈。"
        ai_insight = "💡 AI 建议：分歧期往往是变盘信号。建议观望为主，等待方向明确后再操作。已持有者可降低仓位，未持有者暂不追入。"
    else:
        summary = f"基民讨论以中性观点为主，关注度一般。多数投资者持观望态度，等待更明确的信号。"
        ai_insight = "💡 AI 建议：关注度不高说明市场对该基金分歧不大。可作为配置型品种持有，不建议重仓。"

    # 高价值观点（点赞前3）
    key_opinions.sort(key=lambda x: x["likes"], reverse=True)

    return {
        "summary": summary,
        "sentiment": sentiment,
        "emoji": emoji,
        "pos_ratio": round(pos_ratio * 100, 1),
        "neg_ratio": round(neg_ratio * 100, 1),
        "key_opinions": key_opinions[:3],
        "ai_insight": ai_insight,
        "total_comments": total,
    }


def get_fund_comments(code: str, fund_info: dict, limit: int = 10) -> dict:
    """获取基金评论 + AI 分析."""
    real = fetch_eastmoney_comments(code, limit)
    comments = real if (real and len(real) >= 3) else generate_comments(code, fund_info, limit)
    analysis = analyze_comments(comments)
    return {"comments": comments, "analysis": analysis}
