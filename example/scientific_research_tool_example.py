#!/usr/bin/env python3
"""
Example: SearchUnpaywall with Full Text Retrieval

This script demonstrates how to use the SearchUnpaywall tool with the new
full text retrieval capability. You can configure the maximum number of
characters to retrieve during initialization.
"""

from llm_tool_hub.scientific_research_tool.search_unpaywall import SearchUnpaywall

# Example 1: Basic usage - metadata only
print("=" * 70)
print("Example 1: Search without full text (default)")
print("=" * 70)
tool = SearchUnpaywall()
result = tool.run(doi="10.1038/nature12373")
print(result[:1000] + "\n...\n")

# Example 2: With full text retrieval - default max_chars
print("\n" + "=" * 70)
print("Example 2: Search with full text (default max_chars=100000)")
print("=" * 70)
tool = SearchUnpaywall()
result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
print(result[:1500] + "\n...\n")

# Example 3: Custom max_chars limit
print("\n" + "=" * 70)
print("Example 3: Search with custom max_chars=5000")
print("=" * 70)
tool = SearchUnpaywall(max_chars=5000)
print(f"Tool initialized with max_chars: {tool.max_chars}")
result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
print(result[:1500] + "\n...\n")

# Example 4: Using custom email for API
print("\n" + "=" * 70)
print("Example 4: Search with custom email")
print("=" * 70)
tool = SearchUnpaywall(max_chars=50000)
result = tool.run(
    doi="10.1038/nature12373",
    email="your.email@example.com",
    get_fulltext=True
)
print(result[:1500] + "\n...\n")

print("=" * 70)
print("Summary of Features:")
print("=" * 70)
print("""
1. max_chars parameter:
   - Set during tool initialization
   - Controls maximum characters to retrieve for full text
   - Default: 100000 characters
   - Example: SearchUnpaywall(max_chars=50000)

2. get_fulltext parameter:
   - Set when calling run() method
   - Enables/disables full text retrieval
   - Default: False (backward compatible)
   - Example: tool.run(doi="...", get_fulltext=True)

3. Return behavior:
   - Success: Returns metadata + full text (truncated if needed)
   - Failure: Returns metadata + note about unavailable full text
   - Status: Always includes paper metadata and OA information

4. Supported content types:
   - Plain text (text/plain)
   - HTML (text/html)
   - PDF (application/pdf)
   - Other text-based formats
""")
