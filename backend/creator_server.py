"""CreatorOS Backend — 精简版 FastAPI Server

核心接口:
  POST /chat/stream  SSE 流式内容创作对话
  GET  /             health check
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from langchain_core.messages import HumanMessage

load_dotenv(override=True)

from src.agent import get_creator_graph
from src.graph.state import normalize_markdown

app = FastAPI(title="CreatorOS", version="1.0", description="AI 内容创作多智能体工作台")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


NODE_LABELS = {
    "router": "分析创作意图",
    "handoff": "准备创作上下文",
    "discovery": "选题发现分析中",
    "script": "脚本撰写中",
    "adapt": "多平台改编中",
    "review": "内容质量审核中",
    "chat": "AI 创作助手应答中",
    "discovery_worker": "启动选题Agent",
    "script_worker": "启动脚本Agent",
    "adapt_worker": "启动改编Agent",
    "review_worker": "启动审核Agent",
    "chat_worker": "启动对话Agent",
}


@app.get("/")
async def root():
    return {"status": "ok", "service": "CreatorOS", "version": "1.0"}


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    """SSE 流式内容创作对话"""
    session_id = payload.session_id or f"sess-{uuid.uuid4().hex[:12]}"

    graph = get_creator_graph()
    messages = [HumanMessage(content=payload.message)]

    async def event_generator():
        accumulated = ""

        yield {
            "event": "meta",
            "data": json.dumps({"session_id": session_id, "status": "processing"}, ensure_ascii=False),
        }

        try:
            # Stream node status events
            async for event in graph.astream_events(
                {"messages": messages},
                {"configurable": {"thread_id": session_id}},
                version="v2",
            ):
                kind = event.get("event", "")
                name = event.get("name", "")

                # Token-level streaming from chat model
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk:
                        content = getattr(chunk, "content", "")
                        if isinstance(content, list):
                            content = "".join(
                                t.get("text", "") if isinstance(t, dict) else str(t)
                                for t in content
                            )
                        if content and isinstance(content, str) and content.strip():
                            accumulated += content
                            yield {"event": "chunk", "data": content}

                # Node start → status update
                elif kind == "on_chain_start" and name in NODE_LABELS:
                    yield {
                        "event": "status",
                        "data": json.dumps(
                            {"node": name, "label": NODE_LABELS[name], "status": "running"},
                            ensure_ascii=False,
                        ),
                    }

            # Also extract generation from final state as fallback
            if not accumulated:
                try:
                    config = {"configurable": {"thread_id": session_id}}
                    state = graph.get_state(config)
                    if state and state.values:
                        gen = state.values.get("generation", "")
                        if gen:
                            accumulated = gen
                            yield {"event": "chunk", "data": gen}
                except Exception:
                    pass

            fixed = normalize_markdown(accumulated) if accumulated else "Agent 已完成处理"
            yield {
                "event": "done",
                "data": json.dumps(
                    {"session_id": session_id, "answer": fixed},
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    print(">>> 启动 CreatorOS 后端服务...")
    print(">>> http://localhost:8003")
    uvicorn.run("creator_server:app", host="0.0.0.0", port=8003)
