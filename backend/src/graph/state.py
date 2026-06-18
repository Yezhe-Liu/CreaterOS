"""CreatorOS StateGraph 状态定义 — 内容创作 Multi-Agent

CreatorState (主图):
  - messages        全局对话 (add_messages reducer)
  - intent          创作意图: discovery / script / adapt / review / chat
  - content_topic   用户的创作主题
  - script_type     脚本类型: 口播/剧情/评测/教程
  - platforms       目标平台列表
  - worker_input    传给 Worker 的上下文
  - generation      Worker 回传的生成内容 (与 WorkerState 共享字段名)

WorkerState (子图基类):
  - messages        子图内部消息
  - worker_input    Supervisor 传入的上下文
  - generation      最终生成文本
"""

from __future__ import annotations

from typing import Annotated, Any, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


# =============================================================================
# CreatorState — 主图状态
# =============================================================================

class CreatorState(TypedDict):
    """CreatorOS 主图全局状态"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    intent: str              # discovery / script / adapt / review / chat
    intent_reasoning: str    # router 分类理由
    content_topic: str       # 用户创作主题
    script_type: str         # 口播/剧情/评测/教程
    platforms: list[str]     # 目标平台
    worker_input: dict[str, Any]  # 构建后传给 Worker 子图
    generation: str               # Worker 回传的生成内容


# =============================================================================
# Worker 子图状态
# =============================================================================

class WorkerState(TypedDict):
    """Worker 子图基类状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    worker_input: dict[str, Any]
    generation: str


# 各 Worker 专用 State（继承基类语义）
class DiscoveryWorkerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    worker_input: dict[str, Any]
    generation: str


class ScriptWorkerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    worker_input: dict[str, Any]
    generation: str


class AdaptWorkerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    worker_input: dict[str, Any]
    generation: str


class ReviewWorkerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    worker_input: dict[str, Any]
    generation: str


# =============================================================================
# Pydantic Structured Output（只有 Router 需要）
# =============================================================================

class RouterOutput(BaseModel):
    intent: str = Field(
        description=(
            "用户创作意图分类:\n"
            "- 'discovery': 找选题/热点/竞品分析\n"
            "- 'script': 写脚本/文案\n"
            "- 'adapt': 多平台内容改编\n"
            "- 'review': 内容审核/优化\n"
            "- 'chat': 闲聊或功能咨询"
        )
    )
    reasoning: str = Field(description="分类理由")
    content_topic: str = Field(description="提取的创作主题，如无则为空")
    script_type: str = Field(description="脚本类型，如用户未指定则为空")
    platforms: list[str] = Field(description="目标平台，如用户未指定则为空")
