import requests
import json

# 1. 搜索一个你刚才抓取的文章里的词 (比如 "Cookie" 或 "协议")
query = "Cookie" 

print(f"🔍 正在搜索: {query} ...")

url = "http://localhost:8000/search"
payload = {
    "q": query,
    "limit": 3,
    # 2. 测试筛选功能 (假设你刚才抓的是 CSDN/掘金，平台可能是 other 或其他)
    # 如果你不确定平台叫什么，可以先注释掉下面这行 filter_platform
    # "filter_platform": "other", 
}

try:
    resp = requests.post(url, json=payload)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ 搜索成功！找到 {data['total']} 条结果：\n")
        
        for item in data['items']:
            print(f"📄 标题: {item['title']}")
            # 3. 重点检查：有没有 <em> 高亮标签？
            print(f"✨ 片段: {item['snippet']}") 
            print(f"🏷️ 平台: {item['source_platform']}")
            print("-" * 30)
            
        if data['items'] and "<em>" in str(data['items'][0]):
            print("\n🎉 恭喜！高亮 (Highlight) 功能生效了！Step 7 完美通过！")
        else:
            print("\n⚠️ 没看到高亮标签 <em>，请检查 search.py 是否配置了 highlightPreTag")
            
    else:
        print(f"❌ 搜索报错: {resp.text}")

except Exception as e:
    print(f"❌ 请求失败: {e}") 