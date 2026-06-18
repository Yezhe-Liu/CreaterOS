"""CreatorOS Worker 子图模块"""

from __future__ import annotations

from src.graph.workers.base import build_worker_input

__all__ = ["build_worker_input"]

# Worker 名称 → handoff 路由目标的映射
WORKER_ROUTE_MAP: dict[str, str] = {
    "discovery": "discovery_worker",
    "script": "script_worker",
    "adapt": "adapt_worker",
    "review": "review_worker",
    "chat": "chat_worker",
}
