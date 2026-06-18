"""CreatorOS 入口 — 组合根

双模型架构:
  flash_model → router / adapt / review
  pro_model  → discovery / script / chat
"""

from __future__ import annotations

from src.config import get_chat_settings
from src.llm_factory import create_flash_model, create_pro_model

_GRAPH = None
_GRAPH_SIGNATURE: tuple[str, str, str] | None = None


def get_creator_graph():
    """获取编译后的 CreatorOS StateGraph（带模型变更检测缓存）"""
    global _GRAPH, _GRAPH_SIGNATURE

    chat_settings = get_chat_settings()
    signature = (chat_settings.provider, chat_settings.model, chat_settings.model_pro)

    if _GRAPH is not None and _GRAPH_SIGNATURE == signature:
        return _GRAPH

    flash_model = create_flash_model()
    pro_model = create_pro_model()
    print(f"[CreatorOS] provider={chat_settings.provider} flash={chat_settings.model} pro={chat_settings.model_pro}")

    from src.graph.builder import build_creator_graph
    _GRAPH = build_creator_graph(flash_model=flash_model, pro_model=pro_model)
    _GRAPH_SIGNATURE = signature
    return _GRAPH


# 兼容旧入口
def get_agent_graph():
    return get_creator_graph()
