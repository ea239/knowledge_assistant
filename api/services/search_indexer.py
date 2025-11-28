from loguru import logger
from .meili_client import get_index

def to_meili_doc(art) -> dict:
    """
    将 DB 模型转换为 Meilisearch 文档
    Timeline 要求字段: title, content_text, tags, source_platform
    """
    return {
        "id": str(art.id),
        "title": art.title or "",
        # 截取前 20000 字符，防止超级长文拖慢索引速度
        "content_text": (art.content_text or "")[:20000],
        "summary": art.summary or "",
        "source_platform": art.source_platform or "other",
        "tags": art.tags or [],
        # 🌟 新增：时间戳，用于结果排序 (Newest first)
        "created_at": int(art.created_at.timestamp()) if art.created_at else 0
    }

def upsert_article_to_meili(art) -> None:
    try:
        idx = get_index() # 获取索引实例
        # add_documents 是异步/任务式的，不会阻塞太久
        idx.add_documents([to_meili_doc(art)], primary_key="id")
        logger.info(f"✅ [Meili] Synced article: {art.id}")
    except Exception as e:
        # 容错：搜不到不影响存库，记录日志即可
        logger.error(f"❌ [Meili] Sync failed for {art.id}: {e}")