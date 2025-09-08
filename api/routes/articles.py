from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import get_db
from ..models import Article
from ..schemas import ArticleOut

router = APIRouter()

@router.get("/articles", response_model=List[ArticleOut])
def list_articles(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    platform: Optional[str] = None,
):
    q = db.query(Article).order_by(Article.created_at.desc())
    if platform:
        q = q.filter(Article.source_platform == platform)
    items = q.offset(offset).limit(limit).all()
    return items
