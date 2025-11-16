"""
Example 1: Minimal parallel_tool_agent usage

This example is intentionally simple and focuses **only** on the
parallel_tool_agent itself (no ideation integration).

Run this file to see how parallel_tool_agent executes multiple
paper-search queries in parallel using SearchSemanticScholar.
"""

from llm_tool_hub.scientific_research_tool import SearchSemanticScholar
from agent_blocks_hub.parallel_tool_agent import create_parallel_tool_agent


def main() -> None:
    """Run a minimal parallel_tool_agent demo with no LLM summarization."""

    print("\n" + "=" * 80)
    print("PARALLEL TOOL AGENT - MINIMAL EXAMPLE (NO IDEATION)")
    print("=" * 80 + "\n")

    # Create a lightweight parallel tool agent (no LLM needed)
    agent = create_parallel_tool_agent(
        tools=[SearchSemanticScholar()],
        enable_summarization=False,  # Only run tools, no LLM summarizing
        verbose=True,
    )

    queries = [
        "transformer neural networks",
        "attention mechanism in deep learning",
        "BERT language model",
    ]

    print(f"Running {len(queries)} parallel tool calls...\n")

    result = agent.invoke({
        "parallel_tool_agent_messages": queries,
    })

    print("\n" + "=" * 80)
    print("RAW TOOL RESULTS")
    print("=" * 80 + "\n")

    for idx, tool_result in result["tool_results"].items():
        print(f"Query {idx + 1}: {tool_result['query']}")
        print(f"Tool: {tool_result['tool_name']}")
        print(f"Success: {tool_result['success']}")
        print("Result preview:")
        print(tool_result["result"][:400] + "...")
        print("-" * 80)


if __name__ == "__main__":
    main()
