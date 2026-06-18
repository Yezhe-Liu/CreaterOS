"""ChatWorker — 简单对话"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.graph.state import WorkerState

_CHAT_SYSTEM = "你是 CreatorOS，一个 AI 内容创作助手。你帮助短视频博主和内容商家做选题、写脚本、多平台改编和内容审核。请友好简洁地回答用户。"


def create_chat_node(model: BaseChatModel):
    def chat_node(state: WorkerState, config: RunnableConfig) -> dict:
        wi = state.get("worker_input", {})
        user_text = wi.get("query", "")
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        full = ""
        for chunk in model.stream([
            SystemMessage(content=_CHAT_SYSTEM),
            HumanMessage(content=user_text),
        ]):
            full += chunk.content if hasattr(chunk, "content") and chunk.content else ""

        return {"generation": full}

    return chat_node


def build_chat_worker(pro_model: BaseChatModel) -> StateGraph:
    workflow = StateGraph(WorkerState)
    workflow.add_node("chat", create_chat_node(pro_model))
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)
    return workflow.compile(checkpointer=MemorySaver())
