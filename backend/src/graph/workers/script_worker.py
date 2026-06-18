"""ScriptWorker — 脚本撰写"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import ScriptWorkerState
from src.prompts import PromptRegistry

_registry = PromptRegistry.get_instance()


def create_script_node(model: BaseChatModel):
    script_static = _registry.get_static_prefix("script")
    script_dynamic = _registry.get_dynamic_template("script")

    def script_node(state: ScriptWorkerState, config: RunnableConfig) -> dict:
        wi = state.get("worker_input", {})
        user_text = wi.get("query", "")
        topic = wi.get("content_topic", user_text)
        script_type = wi.get("script_type", "口播")
        platform = wi.get("platforms", ["抖音"])[0] if wi.get("platforms") else "抖音"

        full = ""
        for chunk in model.stream([
            SystemMessage(content=script_static),
            HumanMessage(content=script_dynamic.format(
                topic=topic, script_type=script_type, platform=platform, user_text=user_text
            )),
        ], config):
            full += chunk.content if hasattr(chunk, "content") and chunk.content else ""

        return {"generation": full}

    return script_node


def build_script_worker(pro_model: BaseChatModel) -> StateGraph:
    workflow = StateGraph(ScriptWorkerState)
    workflow.add_node("script", create_script_node(pro_model))
    workflow.set_entry_point("script")
    workflow.add_edge("script", END)
    return workflow.compile(checkpointer=MemorySaver())
