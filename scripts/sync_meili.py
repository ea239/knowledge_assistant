from sqlalchemy.orm import Session
from api.db import SessionLocal
from api.models.article import Article
from api.services.search_indexer import upsert_article_to_meili

def sync_all_articles():
    db: Session = SessionLocal()
    try:
        articles = db.query(Article).all()
        print(f"📦 发现数据库中有 {len(articles)} 篇文章，准备同步...")
        
        for art in articles:
            try:
                upsert_article_to_meili(art)
                print(f" -> 已同步: {art.title}")
            except Exception as e:
                print(f" x 失败 {art.id}: {e}")
                
        print("✅ 全量同步完成！")
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_articles()