"""CreatorOS StateGraph 总装器 — Supervisor + Worker 多智能体网络

图拓扑:
  Supervisor
    ├── router           → 创作意图分类
    ├── discovery_worker → 选题发现 (嵌入子图)
    ├── script_worker    → 脚本撰写 (嵌入子图)
    ├── adapt_worker     → 多平台改编 (嵌入子图)
    ├── review_worker    → 内容审核 (嵌入子图)
    └── chat_worker      → 对话 (嵌入子图)

双模型注入:
  flash_model → router, discovery, script, adapt, review (全部结构化任务)
  pro_model  → chat (仅闲聊保留深度推理，降低 TTFB)
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel

from src.graph.supervisor import build_supervisor_graph
from src.graph.workers.discovery_worker import build_discovery_worker
from src.graph.workers.script_worker import build_script_worker
from src.graph.workers.adapt_worker import build_adapt_worker
from src.graph.workers.review_worker import build_review_worker
from src.graph.workers.chat_worker import build_chat_worker
from src.graph.state import CreatorState


def build_creator_graph(
    flash_model: BaseChatModel,
    pro_model: BaseChatModel,
):
    """构建完整的 CreatorOS Multi-Agent 图网络"""
    # 1. 构建主图骨架
    print("[CreatorOS] Assembling Supervisor main graph...")
    supervisor = build_supervisor_graph(flash_model)

    # 2. 编译并嵌入 Worker 子图
    print("[CreatorOS] Compiling DiscoveryWorker...")
    supervisor.add_node("discovery_worker", build_discovery_worker(flash_model))

    print("[CreatorOS] Compiling ScriptWorker...")
    supervisor.add_node("script_worker", build_script_worker(flash_model))

    print("[CreatorOS] Compiling AdaptWorker...")
    supervisor.add_node("adapt_worker", build_adapt_worker(flash_model))

    print("[CreatorOS] Compiling ReviewWorker...")
    supervisor.add_node("review_worker", build_review_worker(flash_model))

    print("[CreatorOS] Compiling ChatWorker...")
    supervisor.add_node("chat_worker", build_chat_worker(pro_model))

    # 3. 补齐 Worker → END 的边
    for name in ["discovery_worker", "script_worker", "adapt_worker", "review_worker", "chat_worker"]:
        supervisor.add_edge(name, END)

    print("[CreatorOS] Compiling graph...")
    compiled = supervisor.compile(checkpointer=MemorySaver())
    print("[CreatorOS] Graph compilation complete.")
    return compiled
