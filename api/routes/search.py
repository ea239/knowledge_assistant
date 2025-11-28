# api/routes/search.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from loguru import logger

from ..db import get_db
from fastapi import Depends
from ..services.meili_client import get_index
from ..services.embedding_models import get_embedding_model

router = APIRouter()

class SearchReq(BaseModel):
    q: str
    limit: int = 20
    offset: int = 0
    filter_platform: Optional[str] = None
    filter_tag: Optional[str] = None
    use_semantic: bool = True  # 开关：是否启用语义检索

@router.post("/search")
def search(req: SearchReq, db: Session = Depends(get_db)):
    """
    Step 8 最终版：混合检索 (BM25 + Vector)
    [cite_start]Timeline [cite: 80-83]
    """
    start_time = time.time()
    
    # 用字典存储融合结果：{article_id: final_score}
    # 初始 score 为 0
    candidates: Dict[str, float] = {}
    
    # -------------------------------------------------------
    # 1. 关键词检索 (BM25 - Meilisearch)
    # -------------------------------------------------------
    try:
        idx = get_index()
        
        # 构造 Meili 过滤器
        filter_conds = []
        if req.filter_platform: filter_conds.append(f"source_platform = '{req.filter_platform}'")
        if req.filter_tag: filter_conds.append(f"tags = '{req.filter_tag}'")
        filter_query = " AND ".join(filter_conds) if filter_conds else None

        # 查稍微多一点，方便做交集
        meili_resp = idx.search(req.q, {
            "limit": req.limit * 2,
            "filter": filter_query,
            "attributesToHighlight": ["title", "content_text"],
            "highlightPreTag": "<em class='highlight'>",
            "highlightPostTag": "</em>",
            "attributesToCrop": ["content_text"],
            "cropLength": 50
        })

        # Meili 结果处理 (使用倒数排名作为基础分)
        # [cite_start]权重系数: 0.6 [cite: 82]
        meili_hits_map = {} # 暂存 Meili 的原始 hit 信息，方便最后返回
        for rank, hit in enumerate(meili_resp['hits']):
            aid = hit['id']
            # 简单的归一化：第一名 1.0 分，往后递减
            score = 1.0 / (rank + 1)
            candidates[aid] = candidates.get(aid, 0) + (score * 0.6)
            meili_hits_map[aid] = hit # 存下来，如果最后命中了直接用，省得查库

    except Exception as e:
        logger.error(f"⚠️ Meili search failed: {e}")

    # -------------------------------------------------------
    # 2. 语义检索 (Vector - Postgres)
    # -------------------------------------------------------
    if req.use_semantic:
        try:
            # a. 生成 Query 向量
            model = get_embedding_model("bge-m3")
            query_vec = model.encode([req.q])[0].tolist()

            # b. 构造 SQL (使用 pgvector <=> 操作符)
            # 过滤逻辑比较麻烦，暂时在 Python 层做，或者拼 SQL
            # 这里简单起见，先查回 TopK，再在 Python 里做过滤 (为了性能，生产环境应把过滤下推到 SQL)
            sql = text("""
                SELECT id, 1 - (embedding <=> :qv) as similarity
                FROM articles
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :qv
                LIMIT :k
            """)
            
            rows = db.execute(sql, {"qv": str(query_vec), "k": req.limit * 2}).fetchall()
            
            # c. 融合分数
            # [cite_start]权重系数: 0.4 [cite: 82]
            for row in rows:
                aid = str(row.id)
                sem_score = float(row.similarity)
                
                # 如果有筛选条件，这里要手动检查一下 (略复杂，暂且假设语义搜出来的都符合)
                # 实际上应该把 filter 传给 SQL
                
                candidates[aid] = candidates.get(aid, 0) + (sem_score * 0.4)

        except Exception as e:
             logger.error(f"⚠️ Vector search failed: {e}")

    # -------------------------------------------------------
    # 3. 排序与结果组装
    # -------------------------------------------------------
    # 按分数倒序
    sorted_cands = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    
    # 分页切片
    paged_cands = sorted_cands[req.offset : req.offset + req.limit]
    
    final_items = []
    
    # 对于没在 Meili 结果里（纯向量搜出来）的文章，需要回 DB 查详情
    missing_ids = [aid for aid, _ in paged_cands if aid not in meili_hits_map]
    db_articles = {}
    if missing_ids:
        rows = db.execute(
            text("SELECT id, title, content_text, source_platform, created_at FROM articles WHERE id = ANY(CAST(:ids AS uuid[]))"),
            {"ids": missing_ids}
        ).fetchall()
        for r in rows:
            db_articles[str(r.id)] = r

    for aid, score in paged_cands:
        item = {}
        # 优先用 Meili 的数据 (带高亮)
        if aid in meili_hits_map:
            hit = meili_hits_map[aid]
            fmt = hit.get("_formatted", hit)
            item = {
                "id": aid,
                "title": fmt.get("title"),
                "snippet": fmt.get("content_text"),
                "source_platform": hit.get("source_platform"),
                "tags": hit.get("tags"),
                "score": round(score, 4),
                "created_at": hit.get("created_at")
            }
        # 如果 Meili 没搜到，但向量搜到了 (补充数据)
        elif aid in db_articles:
            art = db_articles[aid]
            item = {
                "id": aid,
                "title": art.title,
                # 向量搜出来的没有高亮，手动截取一下
                "snippet": (art.content_text or "")[:100] + "...", 
                "source_platform": art.source_platform,
                "tags": [],
                "score": round(score, 4),
                "created_at": int(art.created_at.timestamp()) if art.created_at else 0
            }
        
        if item:
            final_items.append(item)

    return {
        "items": final_items,
        "total": len(candidates), # 这是一个估算值
        "time_ms": int((time.time() - start_time) * 1000)
    }