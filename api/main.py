from fastapi import FastAPI
from .routes import articles, health, ingest, search


app = FastAPI(title="Knowledge Assistant API")

app.include_router(articles.router)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(search.router)