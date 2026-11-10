import asyncio
from types import SimpleNamespace


def test_summarizer_uses_configured_per_message_limit():
    async def run():
        import sys
        from types import ModuleType
        openai = ModuleType("openai")
        openai.AsyncOpenAI = object
        sys.modules.setdefault("openai", openai)
        mcp = ModuleType("mcp")
        mcp.ClientSession = object
        mcp.StdioServerParameters = object
        sys.modules.setdefault("mcp", mcp)
        mcp_client = ModuleType("mcp.client")
        sys.modules.setdefault("mcp.client", mcp_client)
        mcp_stdio = ModuleType("mcp.client.stdio")
        mcp_stdio.stdio_client = object
        sys.modules.setdefault("mcp.client.stdio", mcp_stdio)
        from workbench.agent import Agent

        captured = {}

        class Completions:
            async def create(self, **kwargs):
                captured.update(kwargs)
                message = SimpleNamespace(content="test summary")
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=message)], usage=None
                )

        agent = Agent.__new__(Agent)
        agent.runtime_settings = {"summary_message_max_chars": 5000}
        agent.llm = SimpleNamespace(
            chat=SimpleNamespace(completions=Completions())
        )

        await agent._summarize(
            "test-model",
            [{"role": "tool", "content": "X" * 12000}],
            "",
        )

        transcript = captured["messages"][1]["content"]
        assert len(transcript) == len("Результат инструмента: ") + 5000
        assert transcript.endswith("X" * 5000)

    asyncio.run(run())
