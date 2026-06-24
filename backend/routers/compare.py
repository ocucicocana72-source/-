"""对比 API 路由 — 多基金横向对比 + 行业板块对比."""

from fastapi import APIRouter, Query
from models.schemas import CompareRequest
from services.comparator import compare_funds
from services.fund_fetcher import get_fund_holdings

router = APIRouter()


@router.post("/funds")
async def compare_multiple_funds(req: CompareRequest):
    """多基金横向对比 — 批量获取指标 + 评分 + 持仓."""
    if not req.codes or len(req.codes) < 2:
        return {"error": "至少需要2只基金进行对比"}
    if len(req.codes) > 5:
        return {"error": "最多支持5只基金同时对比"}
    return compare_funds(req.codes, req.period)


@router.get("/sectors")
async def compare_sectors(codes: str = Query("", description="基金代码，逗号分隔")):
    """对比多只基金的持仓行业分布."""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {"error": "请提供基金代码"}
    results = []
    for code in code_list[:5]:
        holdings = get_fund_holdings(code)
        results.append({"code": code, "holdings": holdings[:10], "count": len(holdings)})
    return {"funds": results, "count": len(results)}
