FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p data

# 暴露端口（Railway 会通过 $PORT 环境变量分配实际端口）
EXPOSE ${PORT:-8000}

# 启动命令 — 使用 Railway 分配的端口
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
