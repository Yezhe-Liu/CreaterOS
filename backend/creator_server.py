"""CreatorOS Backend — 精简版 FastAPI Server

核心接口:
  POST /chat/stream  SSE 流式内容创作对话
  GET  /             health check
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from langchain_core.messages import HumanMessage

load_dotenv(override=True)

from src.agent import get_creator_graph

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


@app.get("/")
async def root():
    return {"status": "ok", "service": "CreatorOS", "version": "1.0"}


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    """SSE 流式内容创作对话"""
    session_id = payload.session_id or f"sess-{uuid.uuid4().hex[:12]}"

    async def event_generator():
        graph = get_creator_graph()
        messages = [HumanMessage(content=payload.message)]
        accumulated = ""

        yield {
            "event": "meta",
            "data": json.dumps({"session_id": session_id, "status": "processing"}, ensure_ascii=False),
        }

        try:
            async for event in graph.astream_events(
                {"messages": messages},
                {"configurable": {"thread_id": session_id}},
                version="v2",
            ):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        text = chunk.content
                        accumulated += text
                        yield {"event": "chunk", "data": text}

                elif kind == "on_chain_start":
                    name = event.get("name", "")
                    yield {
                        "event": "status",
                        "data": json.dumps({"node": name, "status": "running"}, ensure_ascii=False),
                    }

            yield {
                "event": "done",
                "data": json.dumps({"session_id": session_id, "answer": accumulated}, ensure_ascii=False),
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
    uvicorn.run("creator_server:app", host="0.0.0.0", port=8003, reload=True)
