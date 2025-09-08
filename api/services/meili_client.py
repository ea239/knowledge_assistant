import os, meilisearch
MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
MEILI_KEY = os.getenv("MEILI_KEY", "masterKey")
INDEX_UID = "articles"
_client = meilisearch.Client(MEILI_URL, MEILI_KEY)

def ensure_index():
    try:
        _client.creat_index(INDEX_UID, {'primaryKey': 'id'})
    except meilisearch.errors.MeiliSearchApiError:
        pass

    idx = _client.index(INDEX_UID)
    idx.update_settings({
        "searchableAttributes": ["title", "content_text", "tags"],
        "filterableAttributes": ["source_platform", "tags"],
        "displayedAttributes": ["id", "title", "summary", "source_platform", "tags", "content_text"]
    })
    return idx