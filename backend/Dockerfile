# 用官方 slim 镜像：体积小、够用。3.12 是当前稳定主流版本。
FROM python:3.12-slim

WORKDIR /app

# 先单独拷依赖清单再装，利用 Docker 层缓存：
# 只要 requirements.txt 没变，重建镜像就不必重新 pip install。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷源码（源码常变，放在依赖层之后）
COPY app ./app

EXPOSE 8000

# --host 0.0.0.0 让容器外能访问；P0 先不开 --reload，跑通为主
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
