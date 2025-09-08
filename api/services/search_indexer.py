from .meili_client import ensure_index

def to_meili_doc(art) -> dict:
    return {
        "id": str(art.id),
        "title": art.title or "",
        "content_text": art.content_text or "",
        "summary": art.summary or "",
        "source_platform": art.source_platform or "",
        "tags": art.tags or [],
    }

def upsert_article_to_meili(art) -> None:
    idx = ensure_index()
    idx.add_documents([to_meili_doc(art)])