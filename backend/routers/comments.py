"""评论 API 路由 — 基民高价值评论."""

from fastapi import APIRouter, Query
from services.comments import get_fund_comments
from services.fund_fetcher import get_fund_info, get_fund_manager, get_fund_nav
from services.calculator import annualized_return, max_drawdown, sharpe_ratio
import pandas as pd

router = APIRouter()


@router.get("/{code}")
async def get_comments(code: str, limit: int = Query(10, ge=1, le=30)):
    """获取基金的基民高价值评论."""
    info = get_fund_info(code)
    manager = get_fund_manager(code)
    nav_data = get_fund_nav(code, "1y")

    fund_info = {"name": info.get("name", code), "manager": manager.get("manager_name", "")}

    if nav_data and len(nav_data) >= 10:
        df = pd.DataFrame(nav_data).sort_values("date")
        returns = df["nav"].pct_change().dropna()
        nav_s = df["nav"]
        fund_info["annualized_return"] = round(annualized_return(returns) * 100, 2)
        fund_info["max_drawdown"] = round(max_drawdown(nav_s) * 100, 2)
        fund_info["sharpe_ratio"] = round(sharpe_ratio(returns), 4)

    result = get_fund_comments(code, fund_info, limit)
    return {"code": code, "comments": result["comments"], "analysis": result["analysis"], "total": len(result["comments"])}
