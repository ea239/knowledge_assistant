# api/routes/ingest.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
from pydantic import BaseModel, HttpUrl  # 👈 1. 新增 HttpUrl 用于校验

from ..db import get_db
from ..models import Article
from ..schemas import IngestTextReq, ArticleOut
from ..services.search_indexer import upsert_article_to_meili

# 👈 2. 引入 parse_url 任务
from worker.task import summarize_article, embed_article, parse_url

router = APIRouter()

# --- 新增的请求模型 (也可以放到 schemas 里，这里为了方便直接写这了) ---
class IngestUrlReq(BaseModel):
    url: HttpUrl

@router.post("/ingest/text", response_model=ArticleOut)
def ingest_text(req: IngestTextReq, db: Session = Depends(get_db)):
    """
    (保持不变) 导入文本 -> 入库 -> 触发任务
    """
    # 1️⃣ 去重检查
    if req.url:
        existing = db.query(Article).filter_by(url=req.url).first()
        if existing:
            raise HTTPException(status_code=400, detail="Article with this URL already exists")

    # 2️⃣ 构建文章对象
    title = req.title or (req.text[:60] + "..." if len(req.text) > 60 else req.text)
    article = Article(
        url=req.url,
        source_platform=req.source_platform,
        title=title,
        content_text=req.text,
        tags=req.tags or [],
        summary=None,
    )

    # 3️⃣ 入库
    db.add(article)
    db.commit()
    db.refresh(article)

    # 4️⃣ 更新全文检索索引
    try:
        upsert_article_to_meili(article)
    except Exception as e:
        logger.warning(f"⚠️ [Meili] Index update failed: {e}")

    # 5️⃣ 启动 Celery 异步任务
    try:
        summarize_article.delay(str(article.id))
        embed_article.delay(str(article.id))
        logger.info(f"📨 [Celery] Queued tasks for {article.id}")
    except Exception as e:
        logger.error(f"❌ [Celery] Failed to enqueue tasks: {e}")

    return article



@router.post("/ingest/url")
def ingest_url(req: IngestUrlReq):
    """
    接收 URL -> 丢给 Celery 爬虫 -> 立即返回
    后续流程：爬虫抓取 -> 入库 -> 自动触发 Embedding/Summary
    """
    # HttpUrl 转字符串
    url_str = str(req.url)
    logger.info(f"🔌 API received URL to parse: {url_str}")
    
    # 🚀 异步触发解析任务 (Fire and Forget)
    # 我们不等待爬虫结果，直接告诉用户“已接收请求”
    task = parse_url.delay(url_str)
    
    return {
        "status": "accepted",
        "message": "URL parsing started in background",
        "url": url_str,
        "task_id": str(task.id)
    }