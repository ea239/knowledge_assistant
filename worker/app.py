import os
import socket
from celery import Celery
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# 1. 获取配置
raw_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 2. 智能主机名检测
REDIS_URL = raw_redis_url
# 只有当包含 "redis" 且不包含 "localhost/127.0.0.1" 时才检测
if "redis" in raw_redis_url and "localhost" not in raw_redis_url and "127.0.0.1" not in raw_redis_url:
    try:
        # 提取主机名 (例如 redis://redis:6379 -> redis)
        if "@" in raw_redis_url:
            hostname = raw_redis_url.split("@")[-1].split(":")[0]
        else:
            hostname = raw_redis_url.split("://")[-1].split(":")[0]
            
        # 尝试解析
        socket.gethostbyname(hostname)
    except:
        logger.warning(f"⚠️  Local env detected: fallback Redis from '{hostname}' to 'localhost'")
        # 🛠️ 修复点：直接使用标准的本地 Redis 地址，而不是 replace
        # 这样避免把 redis:// 协议头也给替换错了
        REDIS_URL = "redis://localhost:6379/0"

# 3. 初始化 Celery
celery_app = Celery(
    "knowledge_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    imports=["worker.task"],
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_ignore_result=False,
    broker_connection_retry_on_startup=True
)

logger.info(f"🥕 Celery connected to: {REDIS_URL}")