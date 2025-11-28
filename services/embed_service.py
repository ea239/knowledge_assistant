import time
from sqlalchemy.orm import Session
from loguru import logger

# 这里的引用路径不用变，因为 api 还是在根目录下
from api.db import SessionLocal
from api.models.article import Article
# 引用我们在 api/services 里写好的底层工具
from api.services.embedding_models import get_embedding_model

def generate_embedding_for_article(article_id: str):
    """
    [业务逻辑层]
    为单篇文章生成 Embedding 并存入数据库。
    此函数既可以被 API 直接调用（同步），也可以被 Celery Worker 调用（异步）。
    """
    # 1. 初始化 DB 会话
    db: Session = SessionLocal()
    try:
        # 2. 获取数据
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"❌ [Business] Article not found: {article_id}")
            return None

        # 3. 业务规则检查：是否已存在？
        # (根据需求，这里策略是：如果有就跳过。如果想支持“重新生成”，可以删掉这几行)
        if article.embedding:
            logger.info(f"⏭️  [Business] Article {article_id} already has embedding. Skipping.")
            return article.embedding

        # 4. 数据预处理规则
        # 优先用摘要，没摘要用正文，截断 8000 字符防止爆显存
        text_to_embed = article.summary if article.summary else (article.content_text or "")[:8000]
        
        if not text_to_embed.strip():
            logger.warning(f"⚠️ [Business] Article {article_id} is empty.")
            return None

        # 5. 调用底层工具 (Infrastructure)
        # 这里调用的是 api/services/embedding_models.py
        model = get_embedding_model("bge-m3") 
        
        logger.info(f"🧠 [Business] Embedding article: {article.title[:20]}...")
        start_time = time.time()
        
        # 6. 执行计算
        embeddings = model.encode([text_to_embed]) 
        embedding_vector = embeddings[0].tolist() 
        
        duration = time.time() - start_time
        logger.success(f"✅ [Business] Embedded in {duration:.2f}s")

        # 7. 落库
        article.embedding = embedding_vector
        db.commit()
        
        return embedding_vector

    except Exception as e:
        logger.error(f"❌ [Business] Failed to embed {article_id}: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

# ============================
# 本地测试入口
# ============================
if __name__ == "__main__":
    # 确保我们在根目录下运行 python -m services.embed_service
    print("💡 请填入真实的 UUID 测试")
    # test_id = "你的UUID"
    # generate_embedding_for_article(test_id)