"""Worker 子图基类工具"""

from __future__ import annotations

from typing import Any


def build_worker_input(supervisor_state: dict[str, Any]) -> dict[str, Any]:
    """从 CreatorState 构建 worker_input 上下文字典。

    只提取 Worker 需要的字段，不传递整个 Supervisor 状态。
    """
    return {
        "query": supervisor_state.get("content_topic", ""),
        "intent": supervisor_state.get("intent", "chat"),
        "content_topic": supervisor_state.get("content_topic", ""),
        "script_type": supervisor_state.get("script_type", "口播"),
        "platforms": supervisor_state.get("platforms", ["抖音"]),
        "original_content": supervisor_state.get("worker_output", ""),
    }
