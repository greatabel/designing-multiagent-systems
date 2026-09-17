#!/usr/bin/env python3
"""
简单的轮转编排示例：中文现代诗 诗人 × 评论家。

命令行模式（默认）：
    python round-robin.py

Web UI 模式：
    python round-robin.py --web
"""

import argparse
import asyncio
import os

from picoagents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.orchestration import RoundRobinOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination


def get_orchestrator():
    """演示轮转对话流程：诗人写作，评论家评审，迭代改进。"""

    client = OpenAIChatCompletionClient(
        model="deepseek-v4-flash",
        base_url="http://10.248.60.236:5000/v1",
        api_key=os.environ["DEEPSEEK_OPENAI_API_KEY"],
    )

    # 诗人：负责创作和修改现代诗
    poet = Agent(
        name="poet",
        description="中文现代诗诗人，擅长意象和凝练的语言。",
        instructions="""你是一位中文现代诗诗人。请用中文创作现代诗，
语言凝练、意象鲜明、有真情实感，不拘泥于格律但要有节奏感。
当收到评论家的修改建议时，认真吸收并重写整首诗（输出完整的新版本，不要只输出修改的部分）。""",
        model_client=client,
    )

    # 评论家：负责评审，满意时输出【通过】
    critic = Agent(
        name="critic",
        description="现代诗评论家，提供具体、有建设性的修改意见。",
        instructions="""你是一位中文现代诗评论家。看到一首诗时，请提出 2-3 条具体、可操作的修改建议，
重点关注：意象是否新鲜、语言是否有赘余、情感是否真挚、节奏是否流畅。
意见要建设性且简短。
如果你认为这首诗已经足够好、之前的意见都已被采纳，请只回复：【通过】""",
        model_client=client,
    )

    # 终止条件：最多 8 条消息（保险丝），或评论家说出【通过】（完成信号）
    termination = MaxMessageTermination(max_messages=8) | TextMentionTermination(
        text="【通过】"
    )

    # 编排器：诗人先写，评论家后评，轮流进行
    orchestrator = RoundRobinOrchestrator(
        agents=[poet, critic], termination=termination, max_iterations=4
    )

    return orchestrator


orchestrator = get_orchestrator()


async def main():
    task = "写一首关于春天樱花的现代诗"
    print(f"🎯 任务: {task}")
    print("🔄 诗人与评论家协作:\n")

    stream = orchestrator.run_stream(task)

    async for message in stream:
        print(f"========\n{message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="轮转编排示例：中文现代诗 诗人与评论家"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动 Web UI 而不是命令行模式",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8070,
        help="Web UI 端口（默认: 8070）",
    )
    args = parser.parse_args()

    if args.web:
        from picoagents.webui import serve

        print("🚀 启动 PicoAgents WebUI（轮转编排）...")
        print(f"\n📋 诗人与评论家协作")
        print(f"  • 端口: {args.port}")
        print(f"  • 试试: '写一首关于春天樱花的现代诗'\n")

        serve(
            entities=[orchestrator],
            port=args.port,
            auto_open=True,
        )
    else:
        asyncio.run(main())
