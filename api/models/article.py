from sqlalchemy import Column, Text, TIMESTAMP, func, CHAR
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
from ..db import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    url = Column(Text(), unique=True, nullable=True)
    source_platform = Column(Text(), nullable=True)
    title = Column(Text(), nullable=False)
    author = Column(Text(), nullable=True)
    published_at = Column(TIMESTAMP(timezone=True), nullable=True)
    content_text = Column(Text(), nullable=True)
    content_html = Column(Text(), nullable=True)
    summary = Column(Text(), nullable=True)
    tags = Column(ARRAY(Text()), nullable=True)
    hash = Column(CHAR(64), nullable=True)
    embedding = Column(Vector(1024), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
