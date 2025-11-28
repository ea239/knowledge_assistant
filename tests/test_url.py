import requests
import time

# 随便找个好抓取的网页，这里用 Python 维基百科
# 你也可以换成你自己写的博客，或者公众号文章链接
target_url = "https://mp.weixin.qq.com/s/uxpV0QVMjhGe3aa_0w6BHQ"

print(f"🔌 发送 URL: {target_url}")

try:
    # 1. 调用 API
    resp = requests.post(
        "http://localhost:8000/ingest/url", 
        json={"url": target_url}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ API 接收成功! 任务 ID: {data['task_id']}")
        print("⏳ 请观察 Worker 窗口的日志滚动...\n")
    else:
        print(f"❌ API 报错: {resp.text}")

except Exception as e:
    print(f"❌ 请求失败: {e}")