# init_meili.py
import time
from api.services.meili_client import client, INDEX_UID

def init_meili():
    print(f"⚙️ 开始配置 Meilisearch 索引: {INDEX_UID} ...")

    # 1. 确保索引存在 (修正了你的拼写错误 create_index)
    try:
        client.create_index(INDEX_UID, {'primaryKey': 'id'})
        print("✅ 索引创建成功 (或已存在)")
    except Exception as e:
        # 如果索引已存在，会报错，忽略即可
        print(f"ℹ️ 索引检查: {e}")

    # 等待一小会儿让索引创建生效
    time.sleep(1)
    
    idx = client.index(INDEX_UID)

    # 2. 更新配置 (Timeline Step 7 要求)
    print("⚙️ 更新字段设置...")
    task = idx.update_settings({
        # 允许搜索的字段 (加入了 summary)
        "searchableAttributes": ["title", "content_text", "summary", "tags"],
        
        # [cite_start]允许筛选的字段 (Timeline 要求: platform, tags) [cite: 72]
        "filterableAttributes": ["source_platform", "tags", "id"],
        
        # 允许排序的字段 (新增: 按时间倒序)
        "sortableAttributes": ["created_at"],
        
        # 拼写纠错容忍度 (可选优化)
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {"oneTypo": 5, "twoTypos": 9}
        }
    })
    
    # 注意：用 .task_uid 而不是 ['taskUid']
    print(f"✅ 配置任务已提交，Task UID: {task.task_uid}")
    print("🎉 Meilisearch 初始化完成！你不需要每次启动项目都运行此脚本。")

if __name__ == "__main__":
    init_meili()