from fastapi import APIRouter 
from worker.task import parse_url, summarize_article 
router = APIRouter() 
@router.post("/ingest/url") 

def ingest_url(payload: dict):
    url = payload["url"] 
    # 1. 写入最基本记录 
    # 2. 入队异步任务 
    parse_url.delay(url) 
    return {"status": "queued", "url": url}