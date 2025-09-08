from pydantic import BaseModel
from typing import Optional

class SearchReq(BaseModel):
    q: str = ""
    k: int = 20
    filter_platform: Optional[str] = None