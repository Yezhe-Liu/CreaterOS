"""CreatorOS 终端验证 — 测试核心创作链路"""
import asyncio
import io
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from langchain_core.messages import HumanMessage
from src.agent import get_creator_graph


def _extract_generation(result: dict) -> str:
    """从图输出中提取 Worker 生成的内容"""
    gen = result.get("worker_output", "") or result.get("generation", "")
    if gen:
        return gen[:1500]

    # 回退: 从 messages 中找最后 AI 消息
    msgs = result.get("messages", [])
    for m in reversed(msgs):
        if hasattr(m, "content") and m.content and hasattr(m, "type") and m.type in ("ai", "assistant"):
            return m.content[:1500]
    return "(未找到生成内容)"


async def test_intent(intent_label: str, user_input: str):
    print(f"\n{'='*60}")
    print(f"测试: {intent_label}")
    print(f"输入: {user_input}")
    print(f"{'='*60}")

    graph = get_creator_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=user_input)]},
        {"configurable": {"thread_id": f"test-{intent_label}"}},
    )

    print(f"意图: {result.get('intent', '?')}")
    print(f"主题: {result.get('content_topic', '?')}")
    output = _extract_generation(result)
    # 安全输出 (GBK 终端可能无法打印 emoji)
    try:
        print(f"输出:\n{output}")
    except UnicodeEncodeError:
        print(f"输出: (含 emoji, {len(output)} 字符) - 生成成功")
    print("-" * 60)
    return result


async def main():
    print("CreatorOS 核心链路验证")
    print("=" * 60)

    # 测试 1: 选题发现
    await test_intent("选题发现", "我要做一期关于'租房避坑'的短视频，帮我分析选题")

    # 测试 2: 脚本撰写
    await test_intent("脚本撰写", "帮我写一个手机评测的口播脚本，评测对象是最新发布的旗舰机")

    # 测试 3: 多平台改编
    await test_intent("多平台改编", "把这段内容改成小红书版：\n「5个让你变穷的消费习惯：1.每天一杯奶茶，一年花掉5000块；2.开各种会员但从来不用...」")

    # 测试 4: 内容审核
    await test_intent("内容审核", "帮我校审这段短视频文案：\n「震惊！这个减肥药三天瘦10斤！不买后悔一辈子！链接在评论区！」")

    print("\n" + "=" * 60)
    print("4 条链路验证完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
