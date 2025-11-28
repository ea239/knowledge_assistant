import requests

# 1. 这是一个纯语义查询
# 你并没有任何文章包含 "http状态保持" 这几个字
# 但是你有一篇关于 "Cookie/Session" 的文章
query = "http状态保持" 

print(f"🧠 正在进行语义搜索: {query} ...")

resp = requests.post("http://localhost:8000/search", json={
    "q": query,
    "limit": 5,
    "use_semantic": True # 开启魔法
})

data = resp.json()
print(f"✅ 找到 {len(data['items'])} 条结果:\n")

for item in data['items']:
    print(f"📄 [{item['score']}] {item['title']}")
    print(f"   Snippet: {item['snippet']}")
    print("-" * 30) 