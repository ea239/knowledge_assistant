from loguru import logger
from worker.app import celery_app
from api.db import SessionLocal
from api.models.article import Article

# ✅ 引入刚才写好的业务逻辑
from services.crawler import parse_article_from_url
from services.embed_service import generate_embedding_for_article
from api.services.search_indexer import upsert_article_to_meili

@celery_app.task(name="worker.tasks.parse_url")
def parse_url(url: str):
    logger.info(f"📥 [Task] Parsing URL: {url}")
    
    # 1. 爬取
    data = parse_article_from_url(url)
    if not data:
        return "Parse Failed"
    
    db = SessionLocal()
    try:
        # 2. 查重
        existing = db.query(Article).filter(Article.url == data["url"]).first()
        if existing:
            # 💡 补救措施：如果 URL 已存在，顺手同步一下 Meili，防止漏网之鱼
            upsert_article_to_meili(existing)
            logger.info(f"⏭️ URL exists. Synced to Meili: {existing.title}")
            return f"Skipped: {existing.id}"

        # 3. 入库
        new_article = Article(
            url=data["url"],
            title=data["title"],
            content_text=data["content_text"],
            source_platform=data["source_platform"],
            author=data.get("author")
        )
        db.add(new_article)
        db.commit()
        db.refresh(new_article)
        logger.info(f"💾 Saved article to DB: {new_article.title}")

        # 4. 🔥 同步到 Meilisearch (新增这一步)
        try:
            upsert_article_to_meili(new_article)
        except Exception as e:
            logger.error(f"⚠️ Failed to sync to Meili: {e}")

        # 5. 触发后续任务
        embed_article.delay(str(new_article.id))
        summarize_article.delay(str(new_article.id))
        
        return f"Parsed & Saved: {new_article.id}"

    except Exception as e:
        logger.error(f"❌ DB Error: {e}")
        db.rollback()
    finally:
        db.close()

@celery_app.task(name="worker.tasks.ocr_image")
def ocr_image(s3_key: str):
    logger.info(f"🖼️ [TODO] OCR 图片: {s3_key}")
    # 这里将来写: 下载图片 -> OCR -> 入库
    # 这一步对应 Timeline Step 6


@celery_app.task(name="worker.tasks.embed_article", bind=True, max_retries=3)
def embed_article(self, article_id: str):
    """
    Step 8: 语义检索的核心任务
    调用 services/embed_service 生成向量并存库
    """
    logger.info(f"🚀 [Task] Starting embedding for {article_id}")
    try:
        # 调用核心业务逻辑
        result = generate_embedding_for_article(article_id)
        
        if result:
            logger.success(f"✅ [Task] Embedding generated successfully for {article_id}")
        else:
            logger.warning(f"⚠️ [Task] Embedding finished but returned None (maybe empty text?)")
            
    except Exception as e:
        logger.error(f"❌ [Task] Embedding failed for {article_id}: {e}")
        # 失败自动重试：10秒后重试
        raise self.retry(exc=e, countdown=10)

@celery_app.task(name="worker.tasks.summarize_article")
def summarize_article(article_id: str):
    # 没 API Key 也不怕，先放着。等做了 Step 9 再来填这里。
    logger.info(f"🤖 [TODO] Skip Summary (No LLM API yet): {article_id}")
    # 这里将来写: 调用 DeepSeek/OpenAI -> 生成摘要 -> 更新 DB
