import trafilatura
from loguru import logger
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import random

# 🌟 新增：使用 curl_cffi 替代标准 requests
from curl_cffi import requests

def normalize_url(url: str) -> str:
    if not url: return ""
    if "#" in url: url = url.split("#")[0]
    return url.strip().rstrip("/")

def detect_platform(url: str) -> str:
    # ... (保持你之前的 detect_platform 代码不变) ...
    domain = urlparse(url).netloc.lower()
    platform_map = {
        "weixin.qq.com": "wechat",
        "zhihu.com": "zhihu",
        "juejin.cn": "juejin",
        "csdn.net": "csdn",
        "baike.baidu.com": "baidu_baike",
        "github.com": "github",
    }
    for key, name in platform_map.items():
        if key in domain: return name
    return "other"

def parse_article_from_url(url: str):
    clean_url = normalize_url(url)
    logger.info(f"🕷️ Crawling: {clean_url}")

    downloaded = None

    # 1. 优先尝试 trafilatura (它对很多普通博客支持很好)
    # 但对于微信，我们故意让它失败或跳过，或者直接用下面的增强请求
    try:
        # 如果是微信，trafilatura 大概率会挂，直接跳过进兜底
        if "weixin" not in clean_url: 
            downloaded = trafilatura.fetch_url(clean_url)
    except Exception:
        pass

    # 2. 增强版兜底 (核心修改)
    if not downloaded:
        logger.info(f"🚀 Using curl_cffi (Chrome impersonation) for {clean_url}...")
        try:
            # 随机休眠，模拟真人
            time.sleep(random.uniform(1.0, 2.0))
            
            # 🌟 关键：impersonate="chrome110" 会模拟真实浏览器的 TLS 指纹
            # 这一步能骗过绝大多数反爬 (包括部分微信风控)
            resp = requests.get(
                clean_url, 
                impersonate="chrome110", 
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
                }
            )
            
            if resp.status_code == 200:
                # 微信特定的编码处理
                if "weixin" in clean_url:
                     resp.encoding = "utf-8"
                downloaded = resp.text
            else:
                logger.error(f"❌ Request failed: {resp.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None

    # 3. 提取内容
    if not downloaded: return None
    
    # 🌟 新增：垃圾数据检测
    # 如果抓下来是验证码页面，直接放弃，不要入库
    if "wappoc_appmsgcaptcha" in downloaded or "<title>环境异常</title>" in downloaded:
        logger.warning("⛔ Detected WeChat CAPTCHA/Block. Skipping to avoid garbage data.")
        return None

    try:
        result_json = trafilatura.extract(
            downloaded, 
            include_comments=False, 
            include_tables=True, 
            output_format="json", 
            with_metadata=True
        )

        parsed_data = {}
        if result_json:
            import json
            data = json.loads(result_json)
            parsed_data = {
                "title": data.get("title") or "Untitled",
                "content_text": data.get("text"),
                "source_platform": detect_platform(clean_url),
                "url": clean_url
            }
        else:
            # BS4 兜底
            soup = BeautifulSoup(downloaded, "html.parser")
            title = soup.title.string.strip() if soup.title else "Untitled"
            parsed_data = {
                "title": title,
                "content_text": "", 
                "source_platform": detect_platform(clean_url),
                "url": clean_url
            }
        
        # 再次检查标题是否正常
        if parsed_data["title"] in ["环境异常", "访问过于频繁"]:
             logger.warning("⛔ Detected blocked title. Skipping.")
             return None

        logger.success(f"✅ Parsed: {parsed_data['title']}")
        return parsed_data

    except Exception as e:
        logger.error(f"❌ Parse error: {e}")
        return None