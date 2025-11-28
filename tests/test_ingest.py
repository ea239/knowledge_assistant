import requests

url = "http://localhost:8000/ingest/text"
data = {
    "title": "测试语义检索",
    "text": "RAG（检索增强生成）是一种通过结合外部知识库来增强大模型回答能力的技术。它首先检索相关文档，然后将文档作为上下文喂给模型。",
    "source_platform": "test"
}

try:
    resp = requests.post(url, json=data)
    print("API 返回状态:", resp.status_code)
    print("API 返回内容:", resp.json())
except Exception as e:
    print("请求失败:", e)