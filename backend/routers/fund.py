"""基金数据 API 路由 — 支持多类型 + 动态排序 + 缓存."""

import random                                                         # 随机打乱
from fastapi import APIRouter, Query                                    # 路由和查询参数
from services.fund_fetcher import (                                     # 数据服务
    get_fund_rank, search_funds, get_fund_nav, get_fund_info, get_fund_holdings,
)
from services.cache import get_cached, set_cached                      # 缓存服务

router = APIRouter()                                                   # 创建路由实例


@router.get("/search")                                                 # 搜索基金
async def search(q: str = Query(..., description="搜索关键词")):        # 关键词参数
    results = search_funds(q)                                          # 调用搜索服务
    random.shuffle(results)                                            # 每次打乱顺序
    return {"results": results, "query": q, "total": len(results)}     # 返回搜索结果


@router.get("/list")                                                   # 基金排行
async def list_funds(
    type: str = Query("股票型", description="基金类型"),                 # 类型筛选
    limit: int = Query(50, ge=1, le=200),                              # 返回数量，最大200
):
    cache_key = f"fund_list_{type}_{limit}"                            # 缓存键
    cached = get_cached(cache_key, ttl_seconds=3600)                   # 1小时缓存
    if cached:                                                         # 有缓存
        random.shuffle(cached["funds"])                                # 打乱顺序
        return cached                                                  # 返回缓存

    funds = get_fund_rank(fund_type=type, limit=limit)                 # 获取排行数据
    result = {"funds": funds, "type": type, "total": len(funds)}       # 组装结果
    set_cached(cache_key, result)                                      # 存入缓存
    random.shuffle(result["funds"])                                    # 打乱顺序
    return result                                                      # 返回结果


@router.get("/{code}")                                                 # 基金详情
async def get_detail(code: str):                                       # 路径参数：基金代码
    return get_fund_info(code)                                         # 返回基金信息


@router.get("/{code}/nav")                                             # 净值走势
async def get_nav(
    code: str,                                                         # 基金代码
    period: str = Query("1y", description="区间: 1m/3m/6m/1y/3y/all"),  # 时间区间
):
    data = get_fund_nav(code, period)                                  # 获取净值数据
    return {"code": code, "period": period, "data": data, "count": len(data)}  # 返回走势


@router.get("/{code}/holdings")                                        # 持仓数据
async def get_holdings(code: str):                                     # 基金代码
    holdings = get_fund_holdings(code)                                 # 获取持仓
    return {"code": code, "holdings": holdings, "count": len(holdings)}  # 返回持仓列表
