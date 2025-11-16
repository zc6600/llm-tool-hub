"""
Example: Basic usage of parallel_tool_agent

This example demonstrates the lightweight parallel_tool_agent for fast
information gathering tasks like paper searches.
"""
# Ensure project src directory is on sys.path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from llm_provider import get_llm
from llm_tool_hub.scientific_research_tool import SearchSemanticScholar
from llm_tool_hub.integrations.langchain_adapter import LangchainToolAdapter
from agent_blocks_hub.parallel_tool_agent import create_parallel_tool_agent


def example_without_summarization():
    """
    Example 1: Fast mode without summarization
    
    This is the fastest mode - directly gets tool results without LLM synthesis.
    Perfect for when you just need raw search results quickly.
    """
    print("\n" + "=" * 80)
    print("Example 1: Fast Mode (No Summarization)")
    print("=" * 80 + "\n")
    
    # Initialize LLM (even in fast mode we now route queries through LLM+tools,
    # just without a second summarization pass).
    #
    # LangSmith is already integrated in `get_llm` via `enable_langsmith`.
    # To enable LangSmith tracing for this example, simply set
    #   enable_langsmith=True
    # and make sure your `.env` contains:
    #   LANGSMITH_API_KEY=lsv2_pt_xxx
    #   LANGSMITH_PROJECT=llm-tool-hub  (or any project name you like)
    # When enabled, all LLM calls inside the parallel tool agent will be
    # traced to https://smith.langchain.com under the configured project.
    llm = get_llm(
        temperature=0.3,
        max_tokens=20000,
        enable_langsmith=True,
    )

    # Wrap custom tool as LangChain structured tool for LLM.bind_tools compatibility
    semantic_scholar = SearchSemanticScholar()
    search_tool = LangchainToolAdapter.to_langchain_structured_tool(semantic_scholar)

    # Create agent without *global* summarization (still uses LLM+tools per query)
    agent = create_parallel_tool_agent(
        llm=llm,
        tools=[search_tool],
        enable_summarization=False,  # No second LLM summarization step
        verbose=True,
    )
    
    # Execute parallel queries
    queries = [
        "transformer neural networks",
        "attention mechanism deep learning",
        "BERT language model"
    ]
    
    print(f"Executing {len(queries)} parallel queries...\n")
    
    result = agent.invoke({
        "parallel_tool_agent_messages": queries
    })
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80 + "\n")
    
    for idx, tool_result in result["tool_results"].items():
        print(f"\nQuery {idx + 1}: {tool_result['query']}")
        print(f"Success: {tool_result['success']}")
        print(f"Tool: {tool_result['tool_name']}")
        print(f"Result preview: {tool_result['result'][:300]}...")
        print("-" * 80)


def example_with_summarization():
    """
    Example 2: Summarization mode
    
    Uses LLM to synthesize results into a coherent summary.
    Slower than fast mode but provides intelligent synthesis.
    """
    print("\n" + "=" * 80)
    print("Example 2: Summarization Mode")
    print("=" * 80 + "\n")
    
    # Initialize LLM with LangSmith tracing enabled so that both the
    # tool-augmented calls and the final summarization steps are recorded.
    llm = get_llm(
        temperature=0.3,
        max_tokens=2000,
        enable_langsmith=True,
    )

    # Wrap custom tool as LangChain structured tool
    semantic_scholar = SearchSemanticScholar()
    search_tool = LangchainToolAdapter.to_langchain_structured_tool(semantic_scholar)

    # Create agent with summarization
    agent = create_parallel_tool_agent(
        llm=llm,  # Required for summarization
        tools=[search_tool],
        enable_summarization=True,  # Enable intelligent synthesis
        system_prompt="Focus on recent breakthroughs and practical applications",
        verbose=True
    )
    
    # Execute parallel queries
    queries = [
        "vision transformer applications",
        "self-supervised learning computer vision"
    ]
    
    print(f"Executing {len(queries)} parallel queries with summarization...\n")
    
    result = agent.invoke({
        "parallel_tool_agent_messages": queries
    })
    
    # Display synthesized summary
    print("\n" + "=" * 80)
    print("SYNTHESIZED SUMMARY")
    print("=" * 80 + "\n")
    print(result["final_summary"])
    
    # Original results are still available
    print("\n" + "=" * 80)
    print("ORIGINAL TOOL RESULTS (also available)")
    print("=" * 80 + "\n")
    
    for idx, tool_result in result["tool_results"].items():
        print(f"\nQuery {idx + 1}: {tool_result['query']}")
        print(f"Success: {tool_result['success']}")
        print("-" * 80)


def example_comparison():
    """
    Example 3: Speed comparison
    
    Demonstrates the speed difference between modes.
    """
    import time
    
    print("\n" + "=" * 80)
    print("Example 3: Speed Comparison")
    print("=" * 80 + "\n")
    
    queries = [
        "graph neural networks",
        "reinforcement learning",
        "generative adversarial networks"
    ]

    # Prepare LangChain structured tool once for both agents
    semantic_scholar = SearchSemanticScholar()
    search_tool = LangchainToolAdapter.to_langchain_structured_tool(semantic_scholar)
    
    # Test fast mode (per-query LLM+tools, no global summarization)
    print("Testing Fast Mode (no summarization)...")
    llm_fast = get_llm(
        temperature=0.3,
        max_tokens=2000,
        enable_langsmith=True,
    )
    agent_fast = create_parallel_tool_agent(
        llm=llm_fast,
        tools=[search_tool],
        enable_summarization=False,
        verbose=False,  # Disable verbose for cleaner timing
    )
    
    start_time = time.time()
    result_fast = agent_fast.invoke({
        "parallel_tool_agent_messages": queries
    })
    fast_time = time.time() - start_time
    
    print(f"Fast mode completed in: {fast_time:.2f} seconds")
    
    # Test summarization mode
    print("\nTesting Summarization Mode...")
    llm = get_llm(
        temperature=0.3,
        max_tokens=20000,
        enable_langsmith=True,
    )
    agent_summary = create_parallel_tool_agent(
        llm=llm,
        tools=[search_tool],
        enable_summarization=True,
        verbose=False
    )
    
    start_time = time.time()
    result_summary = agent_summary.invoke({
        "parallel_tool_agent_messages": queries
    })
    summary_time = time.time() - start_time
    
    print(f"Summarization mode completed in: {summary_time:.2f} seconds")
    
    print("\n" + "=" * 80)
    print("SPEED COMPARISON")
    print("=" * 80)
    print(f"Fast mode:         {fast_time:.2f}s")
    print(f"Summarization:     {summary_time:.2f}s")
    print(f"Speed difference:  {summary_time/fast_time:.1f}x")
    print("=" * 80)


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PARALLEL TOOL AGENT - BASIC USAGE EXAMPLES")
    print("=" * 80)
    
    # Run examples
    example_without_summarization()
    
    # Uncomment to run other examples:
    # example_with_summarization()
    # example_comparison()
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
