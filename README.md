# CreatorOS — AI 多智能体内容创作工作台

> 小满摘星计划 AI 实习笔试项目

## 一句话定义

输入一个创作方向，5 分钟输出完整内容包（选题分析 + 脚本 + 4 平台适配版本 + 质量审核），
替代短视频博主/内容种草商家 6-8 小时的重复劳动。

## 技术架构

CreatorOS 是一个 **Supervisor + 4 Worker 主从多智能体系统**：

```
用户输入 → ContentRouter (意图分类)
              │
    ┌─────────┼─────────┬─────────┐
    ▼         ▼         ▼         ▼
Discovery  Script    Adapt    Review
Worker    Worker    Worker   Worker
(选题分析) (脚本撰写) (多平台) (质量审核)
    │         │         │         │
    └─────────┴─────────┴─────────┘
              ▼
         内容包输出
```

- **Supervisor (ContentRouter)**: 识别创作意图，路由到对应 Worker
- **DiscoveryWorker**: 热点分析 + 竞品拆解 + 3 个切入角度
- **ScriptWorker**: 口播/剧情/评测/教程脚本撰写
- **AdaptWorker**: 小红书 / 抖音 / B站 / 快手 四平台改编
- **ReviewWorker**: 标题评分 + 完播率预估 + 违禁词检查 + SEO 优化

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 编排 | LangGraph (StateGraph) |
| 模型 | DeepSeek V4 Pro + Flash 双模型 |
| 后端 | FastAPI + SSE 流式输出 |
| 前端 | React + TypeScript + Vite |
| 知识库 | ChromaDB (预留) |

## 快速启动

```bash
# 1. 后端
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 填入 DEEPSEEK_API_KEY
python creator_server.py  # → http://localhost:8003

# 2. 前端
cd front1
npm install
npx vite --port 5173  # → http://localhost:5173
```

## Prompt 工作流

所有 Agent Prompt 位于 `backend/src/prompts/__init__.py`，采用 vLLM 静态前缀缓存对齐设计。

核心流程：
1. **Router** → 意图分类为 discovery/script/adapt/review
2. **DiscoveryWorker** → 选题价值分析 + 3 个切入角度 + 竞品对标
3. **ScriptWorker** → 黄金前 3 秒钩子 + 正文 + 互动引导 + 拍摄提示
4. **AdaptWorker** → 4 平台差异化改写（标题/正文/标签策略）
5. **ReviewWorker** → 5 维评分（标题/完播率/互动/违禁词/SEO）

## Demo 视频

<a href="https://github.com/Yezhe-Liu/CreaterOS/blob/master/demo/demo.mp4">
  <img src="https://img.shields.io/badge/▶️-观看_Demo_演示-a78bfa?style=for-the-badge" alt="观看 Demo">
</a>

> 点击上方按钮观看 CreatorOS 完整演示（3分钟）：从输入创作方向到输出选题分析、脚本、4平台改编、质量审核。
