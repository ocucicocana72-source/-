"""基金智能分析助手 — FastAPI 入口."""

import os                                                             # 环境变量
from fastapi import FastAPI                                           # Web 框架
from fastapi.middleware.cors import CORSMiddleware                     # 跨域支持
from contextlib import asynccontextmanager                            # 生命周期
from routers import fund, analysis, news, compare, comments, portfolio  # 业务路由模块
from services.scheduler import start_scheduler, stop_scheduler         # 定时任务

# 允许的前端域名
ALLOWED_ORIGINS = [
    "http://localhost:3000",                                          # 本地开发
    os.getenv("FRONTEND_URL", ""),                                    # 生产环境前端域名
]

@asynccontextmanager
async def lifespan(app):                                              # 应用生命周期
    start_scheduler()                                                 # 启动定时任务
    yield                                                             # 运行应用
    stop_scheduler()                                                  # 停止定时任务

app = FastAPI(                                                        # 创建应用实例
    title="基金智能分析助手",                                          # API 文档标题
    description="支付宝基金深度分析、新闻情感分析、投资建议",            # API 描述
    version="0.2.0",                                                  # 版本号
    lifespan=lifespan,                                                # 生命周期管理
)

app.add_middleware(                                                    # 添加 CORS 中间件
    CORSMiddleware,                                                   # 允许前端跨域调用
    allow_origins=[o for o in ALLOWED_ORIGINS if o],                  # 允许的域名
    allow_credentials=True,                                           # 允许携带 cookie
    allow_methods=["*"],                                              # 允许所有 HTTP 方法
    allow_headers=["*"],                                              # 允许所有请求头
)

app.include_router(fund.router, prefix="/api/fund", tags=["基金"])     # 注册基金路由
app.include_router(analysis.router, prefix="/api/analysis", tags=["分析"])  # 注册分析路由
app.include_router(news.router, prefix="/api/news", tags=["新闻"])     # 注册新闻路由
app.include_router(compare.router, prefix="/api/compare", tags=["对比"])  # 注册对比路由
app.include_router(comments.router, prefix="/api/comments", tags=["评论"])  # 注册评论路由
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["持仓"])  # 注册持仓路由


@app.get("/")                                                         # 根路径
async def root():                                                     # 返回欢迎信息
    return {"message": "基金智能分析助手 API", "version": "0.1.0"}     # JSON 响应


@app.get("/health")                                                   # 健康检查
async def health():                                                   # 用于前端探测后端状态
    return {"status": "ok"}                                           # 返回正常状态
