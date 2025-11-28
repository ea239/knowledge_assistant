import os
import socket
import meilisearch
from loguru import logger
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# ==========================================
# 1. 智能 URL 处理
# ==========================================
raw_url = os.getenv("MEILI_URL", "http://localhost:7700")

# 如果配置的是 docker 主机名 'meilisearch'，但在本地跑脚本（解析不了），自动降级为 localhost
if "meilisearch" in raw_url:
    try:
        socket.gethostbyname("meilisearch")
        MEILI_URL = raw_url
    except:
        logger.warning(f"⚠️  Local env detected: creating fallback from 'meilisearch' to 'localhost'")
        MEILI_URL = raw_url.replace("meilisearch", "localhost")
else:
    MEILI_URL = raw_url

# ==========================================
# 2. 智能 Key 处理
# ==========================================
# [cite_start]优先找 MEILI_KEY，找不到就找 MEILI_MASTER_KEY (Timeline [cite: 9] 兼容)
MEILI_KEY = os.getenv("MEILI_KEY") or os.getenv("MEILI_MASTER_KEY", "master_key")
INDEX_UID = "articles"

# ==========================================
# 3. 初始化客户端
# ==========================================
try:
    masked_key = f"{MEILI_KEY[:2]}***{MEILI_KEY[-2:]}" if MEILI_KEY and len(MEILI_KEY) > 4 else "***"
    logger.info(f"🔌 Connecting to Meili at {MEILI_URL} (Key: {masked_key})")
    
    client = meilisearch.Client(MEILI_URL, MEILI_KEY)
except Exception as e:
    logger.error(f"❌ Failed to init Meili client: {e}")
    client = None

def get_index():
    return client.index(INDEX_UID)