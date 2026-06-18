"""ReviewWorker — 内容质量审核"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import ReviewWorkerState
from src.prompts import PromptRegistry

_registry = PromptRegistry.get_instance()


def create_review_node(model: BaseChatModel):
    review_static = _registry.get_static_prefix("review")
    review_dynamic = _registry.get_dynamic_template("review")

    def review_node(state: ReviewWorkerState, config: RunnableConfig) -> dict:
        wi = state.get("worker_input", {})
        content = wi.get("original_content", wi.get("query", ""))

        full = ""
        for chunk in model.stream([
            SystemMessage(content=review_static),
            HumanMessage(content=review_dynamic.format(content=content)),
        ]):
            full += chunk.content if hasattr(chunk, "content") and chunk.content else ""

        return {"generation": full}

    return review_node


def build_review_worker(flash_model: BaseChatModel) -> StateGraph:
    workflow = StateGraph(ReviewWorkerState)
    workflow.add_node("review", create_review_node(flash_model))
    workflow.set_entry_point("review")
    workflow.add_edge("review", END)
    return workflow.compile(checkpointer=MemorySaver())
