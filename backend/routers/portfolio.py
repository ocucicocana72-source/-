"""持仓 API 路由 — 支持图片识别 + 详细信号分析."""

from fastapi import APIRouter, Body, UploadFile, File
from services.portfolio import get_all_holdings, add_holding, remove_holding
from services.signals import analyze_portfolio, analyze_fund
from services.fund_fetcher import get_fund_info
from services.ocr_service import recognize_from_upload

router = APIRouter()


@router.get("/")
async def list_portfolio():
    """获取持仓列表 + 信号分析."""
    holdings = get_all_holdings()
    if not holdings:
        return {"holdings": [], "summary": {"total_value": 0, "total_cost": 0, "total_return": 0, "count": 0}}
    return analyze_portfolio(holdings)


@router.post("/add")
async def add_to_portfolio(code: str = Body(..., embed=True), buy_price: float = Body(..., embed=True), shares: float = Body(0, embed=True), buy_date: str = Body("", embed=True)):
    """手动添加单只基金."""
    info = get_fund_info(code)
    name = info.get("name", code)
    holding = add_holding(code, name, buy_price, shares, buy_date)
    signal = analyze_fund(code, buy_price, name)
    return {"holding": holding, "signal": signal}


@router.post("/upload")
async def upload_portfolio_screenshot(file: UploadFile = File(...)):
    """
    上传支付宝持仓截图，自动识别基金信息.

    支持格式: JPG, PNG, WEBP, GIF (最大10MB)
    """
    content = await file.read()
    result = await recognize_from_upload(content, file.filename)

    if not result["success"]:
        return result

    # 自动添加识别到的基金
    added = []
    for fund in result["funds"]:
        info = get_fund_info(fund["code"])
        name = info.get("name", fund.get("name", fund["code"]))
        holding = add_holding(
            code=fund["code"],
            name=name,
            buy_price=fund.get("buy_price", 0),
            shares=fund.get("shares", 0),
        )
        signal = analyze_fund(fund["code"], fund.get("buy_price", 0), name)
        added.append({"holding": holding, "signal": signal, "recognized": fund})

    return {
        "success": True,
        "message": f"成功识别并添加 {len(added)} 只基金",
        "funds": added,
    }


@router.post("/batch")
async def batch_add(funds: list[dict] = Body(...)):
    """
    批量添加基金.

    每项格式: {"code": "006265", "buy_price": 1.23, "shares": 1000}
    """
    added = []
    for f in funds:
        code = f.get("code", "")
        buy_price = f.get("buy_price", 0)
        shares = f.get("shares", 0)
        if not code:
            continue
        info = get_fund_info(code)
        name = info.get("name", code)
        holding = add_holding(code, name, buy_price, shares)
        signal = analyze_fund(code, buy_price, name)
        added.append({"holding": holding, "signal": signal})

    return {"success": True, "message": f"成功添加 {len(added)} 只基金", "funds": added}


@router.delete("/{code}")
async def remove_from_portfolio(code: str):
    """删除持仓中的基金."""
    if remove_holding(code):
        return {"success": True, "code": code}
    return {"success": False, "error": "未找到该基金"}


@router.get("/signals")
async def get_signals():
    """获取所有持仓的信号汇总."""
    holdings = get_all_holdings()
    if not holdings:
        return {"signals": [], "message": "暂无持仓"}
    result = analyze_portfolio(holdings)
    result["holdings"].sort(key=lambda x: x.get("total_score", 0), reverse=True)
    return result


@router.get("/detail/{code}")
async def get_fund_detail(code: str, buy_price: float = 0):
    """获取单只基金的详细分析报告."""
    holdings = get_all_holdings()
    holding = next((h for h in holdings if h["code"] == code), None)
    if holding:
        buy_price = holding.get("buy_price", buy_price)

    info = get_fund_info(code)
    name = info.get("name", code)
    signal = analyze_fund(code, buy_price, name)

    return {"signal": signal, "holding": holding}
