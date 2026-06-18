"""DiscoveryWorker — 选题发现 & 热点分析"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import DiscoveryWorkerState
from src.prompts import PromptRegistry

_registry = PromptRegistry.get_instance()


def create_discovery_node(model: BaseChatModel):
    discovery_static = _registry.get_static_prefix("discovery")
    discovery_dynamic = _registry.get_dynamic_template("discovery")

    def discovery_node(state: DiscoveryWorkerState, config: RunnableConfig) -> dict:
        wi = state.get("worker_input", {})
        user_text = wi.get("query", "")

        full = ""
        for chunk in model.stream([
            SystemMessage(content=discovery_static),
            HumanMessage(content=discovery_dynamic.format(user_text=user_text)),
        ]):
            full += chunk.content if hasattr(chunk, "content") and chunk.content else ""

        return {"generation": full}

    return discovery_node


def build_discovery_worker(pro_model: BaseChatModel) -> StateGraph:
    workflow = StateGraph(DiscoveryWorkerState)
    workflow.add_node("discovery", create_discovery_node(pro_model))
    workflow.set_entry_point("discovery")
    workflow.add_edge("discovery", END)
    return workflow.compile(checkpointer=MemorySaver())
