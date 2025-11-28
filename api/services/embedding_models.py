"""
Embedding Model Loader
负责提供统一的 get_embedding_model() 接口
并支持模型缓存、不同 embedding 模型类型的扩展。
"""

from functools import lru_cache
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger # 使用 loguru 替代 print

# ================================
# 主入口：通过模型名获取 embedding 模型
# ================================
@lru_cache(maxsize=1) # 通常加载一个就够了，maxsize=1 节省内存
def get_embedding_model(model_name: str = "bge-m3"): # 给个默认值
    """
    获取 embedding 模型（带缓存）。
    """
    
    # 自动检测加速设备 (GPU > MPS > CPU)
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    
    logger.info(f"🖥️ Inference device: {device}")

    try:
        if model_name == "bge-m3":
            return _load_bge_m3(device)
        
        # 允许直接传入 HuggingFace 的模型 ID (作为兜底)
        # 比如 get_embedding_model("shibing624/text2vec-base-chinese")
        logger.info(f"[embedding] Loading generic model: {model_name}...")
        return SentenceTransformer(model_name, device=device)

    except Exception as e:
        logger.error(f"❌ Failed to load model {model_name}: {e}")
        raise e

# ================================
# 模型加载函数
# ================================

def _load_bge_m3(device: str) -> SentenceTransformer:
    """
    加载 BAAI/bge-m3 模型。
    """
    logger.info("[embedding] Loading BGE-M3 model (BAAI/bge-m3)...")
    # [cite_start]这里对应设计文档中的模型选型 [cite: 77]
    return SentenceTransformer("BAAI/bge-m3", device=device)