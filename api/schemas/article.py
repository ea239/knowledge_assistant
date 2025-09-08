from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class IngestTextReq(BaseModel):
    title: Optional[str] = None
    text: str
    source_platform: Optional[str] = "note"
    url: Optional[str] = None
    tags: Optional[List[str]] = []

class ArticleOut(BaseModel):
    id: UUID
    title: Optional[str] = None
    source_platform: Optional[str]
    summary: Optional[str]
    tags: Optional[List[str]] = None
    created_at: datetime
    class Config:
        from_attributes = True
