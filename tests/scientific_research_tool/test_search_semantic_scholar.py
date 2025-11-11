# tests/scientific_research_tool/test_search_semantic_scholar.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_tool_hub.scientific_research_tool.search_semantic_scholar import SearchSemanticScholar


# ==============================================================================
# A. Mock Data Setup
# ==============================================================================

def create_mock_paper(
    paper_id="123456",
    title="Sample Research Paper",
    authors=None,
    year=2023,
    publication_date="2023-01-15",
    citation_count=42,
    abstract="This is a sample abstract for testing purposes.",
    external_ids=None,
    venue="Conference 2023",
):
    """Helper function to create mock paper objects."""
    paper = Mock()
    paper.paperId = paper_id
    paper.title = title
    paper.year = year
    paper.publicationDate = publication_date
    paper.citationCount = citation_count
    paper.abstract = abstract
    paper.venue = venue

    # Setup authors
    if authors is None:
        authors = []
    author_mocks = []
    for author_name in authors:
        author_mock = Mock()
        author_mock.name = author_name
        author_mocks.append(author_mock)
    paper.authors = author_mocks

    # Setup external IDs
    if external_ids is None:
        external_ids = {}
    paper.externalIds = external_ids

    return paper


@pytest.fixture
def search_tool():
    """Fixture to initialize SearchSemanticScholar tool."""
    return SearchSemanticScholar()


# ==============================================================================
# B. Metadata Tests (Tool Contract)
# ==============================================================================

def test_tool_has_required_metadata(search_tool):
    """B.1: Verify tool has all required metadata."""
    assert search_tool.name == "search_semantic_scholar"
    assert search_tool.description is not None
    assert len(search_tool.description) > 0
    assert search_tool.parameters is not None


def test_tool_metadata_format(search_tool):
    """B.2: Verify metadata follows correct JSON Schema format."""
    metadata = search_tool.get_metadata()

    assert metadata["type"] == "function"
    assert metadata["function"]["name"] == "search_semantic_scholar"
    assert "properties" in metadata["function"]["parameters"]
    assert "query" in metadata["function"]["parameters"]["properties"]
    assert "required" in metadata["function"]["parameters"]
    assert "query" in metadata["function"]["parameters"]["required"]


# ==============================================================================
# C. Successful Search Tests (Happy Path)
# ==============================================================================

@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_semantic_scholar_success(mock_scholar_class, search_tool):
    """C.1: Test successful paper search with valid results."""
    # Setup mock
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Create mock papers
    paper1 = create_mock_paper(
        paper_id="arxiv-001",
        title="Deep Learning Advances",
        authors=["Alice Smith", "Bob Johnson", "Charlie Brown"],
        year=2023,
        publication_date="2023-05-10",
        citation_count=150,
        abstract="This paper explores new approaches to deep learning.",
        external_ids={"ArXiv": "2305.12345"},
        venue="NeurIPS 2023",
    )

    paper2 = create_mock_paper(
        paper_id="arxiv-002",
        title="Quantum Computing Fundamentals",
        authors=["Diana Prince", "Eve Adams"],
        year=2023,
        publication_date="2023-06-15",
        citation_count=89,
        abstract="An introduction to quantum computing principles.",
        external_ids={"ArXiv": "2306.54321", "DOI": "10.1234/qc.2023"},
        venue="Quantum Journal",
    )

    # Setup mock search results
    mock_results = Mock()
    mock_results.items = [paper1, paper2]
    mock_scholar.search_paper.return_value = mock_results

    # Execute search
    result = search_tool.run(query="deep learning", limit=2)

    # Assertions
    assert "Title: Deep Learning Advances" in result
    assert "Title: Quantum Computing Fundamentals" in result
    assert "Alice Smith" in result
    assert "2305.12345" in result
    assert "NeurIPS 2023" in result
    assert "Citation Count: 150" in result
    assert "====" in result  # Check separator format


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_respects_limit_parameter(mock_scholar_class, search_tool):
    """C.2: Test that the limit parameter controls result count."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Create 10 mock papers
    papers = [
        create_mock_paper(
            paper_id=f"paper-{i}",
            title=f"Paper {i}",
            authors=[f"Author {i}"],
            citation_count=i * 10,
        )
        for i in range(10)
    ]

    mock_results = Mock()
    mock_results.items = papers
    mock_scholar.search_paper.return_value = mock_results

    # Search with limit=3
    result = search_tool.run(query="machine learning", limit=3)

    # Count how many papers are in the result
    paper_count = sum(1 for i in range(10) if f"Paper {i}" in result)

    assert paper_count == 3, f"Expected 3 papers, but found {paper_count}"


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_with_long_abstract(mock_scholar_class, search_tool):
    """C.3: Test that long abstracts are truncated properly."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Create paper with very long abstract
    long_abstract = "This is a sample abstract. " * 50  # > 500 chars
    paper = create_mock_paper(
        title="Long Abstract Paper",
        abstract=long_abstract,
    )

    mock_results = Mock()
    mock_results.items = [paper]
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="test", limit=1)

    # Check that abstract is truncated with ellipsis
    assert "..." in result
    # Verify length is reasonable (not the full 1500+ chars)
    assert len(result) < 1500


# ==============================================================================
# D. Edge Cases and Error Handling
# ==============================================================================

@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_no_results(mock_scholar_class, search_tool):
    """D.1: Test handling of empty search results."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Mock empty results
    mock_results = Mock()
    mock_results.items = []
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="nonexistent paper xyz123")

    assert "No valid papers found" in result or "No papers found" in result


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_none_results(mock_scholar_class, search_tool):
    """D.2: Test handling when API returns None results."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Mock None results
    mock_results = None
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="test query")

    assert "No papers found" in result


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_api_exception(mock_scholar_class, search_tool):
    """D.3: Test handling of API exceptions."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Mock API exception
    mock_scholar.search_paper.side_effect = RuntimeError("API Error: Rate limited")

    result = search_tool.run(query="test query")

    assert "Error searching papers" in result


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_missing_optional_fields(mock_scholar_class, search_tool):
    """D.4: Test handling of papers with missing optional fields."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Create paper with minimal data
    paper = create_mock_paper(
        paper_id="minimal-paper",
        title="Minimal Paper",
        authors=[],  # No authors
        year=None,  # No year
        publication_date=None,  # No publication date
        citation_count=None,  # No citations
        abstract=None,  # No abstract
        external_ids=None,  # No external IDs
        venue=None,  # No venue
    )

    mock_results = Mock()
    mock_results.items = [paper]
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="test", limit=1)

    # Should still format and return the paper with N/A values
    assert "Title: Minimal Paper" in result
    assert "N/A" in result
    assert "Error" not in result


# ==============================================================================
# E. Integration Tests (with real API calls - marked as slow)
# ==============================================================================

@pytest.mark.slow
@pytest.mark.integration
def test_search_semantic_scholar_real_api():
    """E.1: Integration test with real Semantic Scholar API."""
    tool = SearchSemanticScholar()

    # Search for a common topic that should always have results
    result = tool.run(query="transformer networks", limit=2)

    # Verify result format
    assert "Title:" in result
    assert "Authors:" in result
    assert "Identifiers:" in result
    assert "Error" not in result


# ==============================================================================
# F. Format Tests
# ==============================================================================

@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_output_format(mock_scholar_class, search_tool):
    """F.1: Test that output is properly formatted with expected structure."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    paper = create_mock_paper(
        title="Formatted Output Test",
        authors=["Author One", "Author Two"],
        external_ids={"ArXiv": "2301.99999", "DOI": "10.9999/test"},
    )

    mock_results = Mock()
    mock_results.items = [paper]
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="test", limit=1)

    # Check for expected output sections
    assert "Title:" in result
    assert "Authors:" in result
    assert "Published:" in result
    assert "Citation Count:" in result
    assert "Summary:" in result
    assert "Identifiers:" in result
    assert "Semantic Scholar ID:" in result
    assert "arXiv ID:" in result
    assert "DOI:" in result


@patch('llm_tool_hub.scientific_research_tool.search_semantic_scholar.SemanticScholar')
def test_search_multiple_authors_formatting(mock_scholar_class, search_tool):
    """F.2: Test formatting with multiple authors."""
    mock_scholar = Mock()
    mock_scholar_class.return_value = mock_scholar

    # Create paper with many authors
    many_authors = [f"Author {i}" for i in range(10)]
    paper = create_mock_paper(
        title="Many Authors Paper",
        authors=many_authors,
    )

    mock_results = Mock()
    mock_results.items = [paper]
    mock_scholar.search_paper.return_value = mock_results

    result = search_tool.run(query="test", limit=1)

    # Should show first 5 authors + "et al."
    assert "Author 0" in result
    assert "Author 4" in result
    assert "et al." in result
    assert "(10 total)" in result
