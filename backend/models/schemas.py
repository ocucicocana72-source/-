"""Pydantic 数据模型 — 定义 API 请求/响应结构."""

from pydantic import BaseModel                                         # 数据模型基类
from typing import Optional                                            # 可选类型


# ---- 基金基础信息 ----

class FundBasic(BaseModel):                                            # 基金简要信息
    code: str                                                          # 基金代码，如 "005827"
    name: str                                                          # 基金名称
    fund_type: str                                                     # 基金类型（股票型/混合型等）
    nav: Optional[float] = None                                        # 单位净值
    acc_nav: Optional[float] = None                                    # 累计净值
    nav_date: Optional[str] = None                                     # 净值日期
    daily_return: Optional[float] = None                               # 日涨跌幅 %


class FundDetail(FundBasic):                                           # 基金详细信息
    manager: Optional[str] = None                                      # 基金经理
    company: Optional[str] = None                                      # 基金公司
    establish_date: Optional[str] = None                               # 成立日期
    size: Optional[float] = None                                       # 基金规模（亿元）
    one_year_return: Optional[float] = None                            # 近一年收益 %
    three_year_return: Optional[float] = None                          # 近三年收益 %


# ---- 净值走势 ----

class NavPoint(BaseModel):                                             # 单个净值数据点
    date: str                                                          # 日期 YYYY-MM-DD
    nav: float                                                         # 单位净值
    acc_nav: Optional[float] = None                                    # 累计净值


# ---- 风险指标 ----

class RiskMetrics(BaseModel):                                          # 风险指标集合
    annualized_return: float                                           # 年化收益率 %
    max_drawdown: float                                                # 最大回撤 %
    sharpe_ratio: float                                                # 夏普比率
    volatility: float                                                  # 年化波动率 %
    calmar_ratio: float                                                # Calmar 比率
    downside_risk: float                                               # 下行风险 %


# ---- 基金经理 ----

class FundManager(BaseModel):                                          # 基金经理信息
    name: str                                                          # 经理姓名
    tenure_years: float                                                # 任职年限
    total_return: float                                                # 任职总回报 %
    annualized_return: float                                           # 年化回报 %
    funds_managed: int                                                 # 管理基金数量
    bio: Optional[str] = None                                          # 简介


# ---- 持仓 ----

class Holding(BaseModel):                                              # 单只持仓股票
    stock_name: str                                                    # 股票名称
    stock_code: str                                                    # 股票代码
    percentage: float                                                  # 占净值比例 %
    industry: Optional[str] = None                                     # 所属行业


class HoldingsAnalysis(BaseModel):                                     # 持仓分析结果
    top_holdings: list[Holding]                                        # 前十大持仓
    industry_distribution: dict[str, float]                            # 行业分布 {行业: 占比}
    concentration: float                                               # 持仓集中度 %
    style: str                                                         # 投资风格


# ---- 风格漂移 ----

class StyleDrift(BaseModel):                                           # 风格漂移检测
    original_style: str                                                # 原始风格定位
    current_style: str                                                 # 当前风格
    drift_score: float                                                 # 漂移分数 0-100
    is_drifting: bool                                                  # 是否发生漂移
    description: str                                                   # 漂移描述


# ---- 新闻 ----

class NewsItem(BaseModel):                                             # 单条新闻
    title: str                                                         # 标题
    url: str                                                           # 链接
    source: str                                                        # 来源
    time: str                                                          # 发布时间
    sentiment: str                                                     # 情感标签（利好/利空/中性）
    sentiment_score: float                                             # 情感分数 -1~1
    summary: Optional[str] = None                                      # 摘要


class MarketMood(BaseModel):                                           # 市场情绪指数
    score: float                                                       # 情绪分数 0-100
    label: str                                                         # 情绪标签
    positive_ratio: float                                              # 利好占比
    negative_ratio: float                                              # 利空占比
    neutral_ratio: float                                               # 中性占比
    total_news: int                                                    # 新闻总数


# ---- 评分 ----

class ScoreBreakdown(BaseModel):                                       # 评分明细
    return_score: float                                                # 收益能力分
    risk_score: float                                                  # 风险控制分
    manager_score: float                                               # 基金经理分
    holdings_score: float                                              # 持仓质量分
    sentiment_score: float                                             # 市场情绪分
    total_score: float                                                 # 综合总分
    recommendation: str                                                # 投资建议
    risk_note: str                                                     # 风险提示


# ---- 对比 ----

class CompareRequest(BaseModel):                                       # 对比请求
    codes: list[str]                                                   # 待对比基金代码列表
    period: str = "1y"                                                 # 时间区间，默认1年


class CompareResult(BaseModel):                                        # 对比结果
    funds: list[FundDetail]                                            # 基金详情列表
    metrics: list[RiskMetrics]                                         # 风险指标列表
    scores: list[ScoreBreakdown]                                       # 评分列表
