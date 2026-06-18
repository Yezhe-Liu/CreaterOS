"""AdaptWorker — 多平台内容改编"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import AdaptWorkerState
from src.prompts import PromptRegistry

_registry = PromptRegistry.get_instance()


def create_adapt_node(model: BaseChatModel):
    adapt_static = _registry.get_static_prefix("adapt")
    adapt_dynamic = _registry.get_dynamic_template("adapt")

    def adapt_node(state: AdaptWorkerState, config: RunnableConfig) -> dict:
        wi = state.get("worker_input", {})
        original = wi.get("original_content", "")
        topic = wi.get("content_topic", "")

        full = ""
        for chunk in model.stream([
            SystemMessage(content=adapt_static),
            HumanMessage(content=adapt_dynamic.format(original_content=original, topic=topic)),
        ], config):
            full += chunk.content if hasattr(chunk, "content") and chunk.content else ""

        return {"generation": full}

    return adapt_node


def build_adapt_worker(flash_model: BaseChatModel) -> StateGraph:
    workflow = StateGraph(AdaptWorkerState)
    workflow.add_node("adapt", create_adapt_node(flash_model))
    workflow.set_entry_point("adapt")
    workflow.add_edge("adapt", END)
    return workflow.compile(checkpointer=MemorySaver())
