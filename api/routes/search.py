from fastapi import APIRouter, Body
from ..services.meili_client import ensure_index
from ..schemas import SearchReq

router = APIRouter()
@router.post("/search")
def search(req: SearchReq = Body(...)):
    idx = ensure_index()
    return idx.search(
        req.q,
        {"limit": req.k,
         "filter": req.filters,
         "attributesToHighlight": ["title", "content_text"]}
    )