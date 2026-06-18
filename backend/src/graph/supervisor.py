"""CreatorOS Supervisor 主编排器 — 内容创作意图路由 + Worker 委派

主图拓扑:
  __start__
      │
      ▼
  [router] — 意图分类
      │
      ▼
  [handoff] — 构建 worker_input 上下文
      │
      ├── intent=discovery → discovery_worker
      ├── intent=script    → script_worker
      ├── intent=adapt     → adapt_worker
      ├── intent=review    → review_worker
      └── intent=chat      → chat_worker
            │
            ▼
           END
"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import CreatorState, RouterOutput
from src.prompts import PromptRegistry

_registry = PromptRegistry.get_instance()


def _route_after_handoff(state: dict) -> Literal["discovery_worker", "script_worker", "adapt_worker", "review_worker", "chat_worker"]:
    """根据 intent 分发到对应 Worker"""
    intent = state.get("intent", "chat")
    route_map = {
        "discovery": "discovery_worker",
        "script": "script_worker",
        "adapt": "adapt_worker",
        "review": "review_worker",
    }
    return route_map.get(intent, "chat_worker")


def create_router_node(model: BaseChatModel):
    """意图分类节点"""
    structured_model = model.with_structured_output(RouterOutput)
    router_static = _registry.get_static_prefix("router")
    router_dynamic = _registry.get_dynamic_template("router")

    def router_node(state: CreatorState, config: RunnableConfig) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {"intent": "chat", "intent_reasoning": "无历史消息", "content_topic": ""}

        last_msg = messages[-1]
        user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        response: RouterOutput = structured_model.invoke([
            SystemMessage(content=router_static),
            HumanMessage(content=router_dynamic.format(user_text=user_text)),
        ])

        return {
            "intent": response.intent,
            "intent_reasoning": response.reasoning,
            "content_topic": response.content_topic or user_text,
            "script_type": response.script_type or "口播",
            "platforms": response.platforms or ["抖音"],
        }

    return router_node


def create_handoff_node():
    """构建 worker_input 上下文，桥接 CreatorState → WorkerState"""
    def handoff_node(state: CreatorState, config: RunnableConfig) -> dict[str, Any]:
        messages = state.get("messages", [])
        last_msg = messages[-1]
        query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        return {
            "worker_input": {
                "query": query,
                "intent": state.get("intent", "chat"),
                "content_topic": state.get("content_topic", query),
                "script_type": state.get("script_type", "口播"),
                "platforms": state.get("platforms", ["抖音"]),
                "original_content": state.get("generation", query),
            }
        }
    return handoff_node


def build_supervisor_graph(flash_model: BaseChatModel) -> StateGraph:
    """构建 Supervisor 主图骨架（不含 Worker 嵌入）"""
    workflow = StateGraph(CreatorState)

    workflow.add_node("router", create_router_node(flash_model))
    workflow.add_node("handoff", create_handoff_node())
    workflow.set_entry_point("router")

    # router → handoff（构建 worker_input 后分发）
    workflow.add_edge("router", "handoff")
    workflow.add_conditional_edges("handoff", _route_after_handoff, {
        "discovery_worker": "discovery_worker",
        "script_worker": "script_worker",
        "adapt_worker": "adapt_worker",
        "review_worker": "review_worker",
        "chat_worker": "chat_worker",
    })

    return workflow
