# src/llm_tool_hub/scientific_research_tool/search_semantic_scholar.py

import logging
from typing import Dict, Any, Optional
from semanticscholar import SemanticScholar
from ..base_tool import BaseTool

logger = logging.getLogger(__name__)

__all__ = ['SearchSemanticScholar']


class SearchSemanticScholar(BaseTool):
    """
    A tool to search for academic papers using Semantic Scholar API.
    Returns formatted results with comprehensive paper metadata including title, authors,
    abstract, citation count, publication date, and external identifiers (arXiv ID, DOI, etc.).
    """

    # --- Required Metadata ---
    name: str = "search_semantic_scholar"
    description: str = (
        "Search for academic papers on Semantic Scholar using a query string. "
        "Returns the top results with comprehensive metadata including paper title, authors, "
        "abstract summary, citation count, publication date, and external identifiers (arXiv ID, DOI, etc.). "
        "Use this tool to find relevant research papers across various fields including machine learning, "
        "computer science, biology, physics, and more."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string (e.g., 'transformer neural networks', 'quantum computing', 'CRISPR gene therapy')",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return. Defaults to 5.",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def run(self, query: str, limit: int = 5) -> str:
        """
        Search for papers on Semantic Scholar API.

        Args:
            query (str): Search query string
            limit (int): Maximum number of results to return (default: 5)

        Returns:
            A formatted string listing the search results with paper metadata.
        """
        try:
            # Initialize Semantic Scholar client
            sch = SemanticScholar()

            # Execute search with comprehensive fields
            results = sch.search_paper(
                query,
                limit=min(limit * 2, 50),  # Fetch more to ensure we have enough valid results
                fields=[
                    'paperId',
                    'externalIds',
                    'title',
                    'abstract',
                    'authors',
                    'year',
                    'publicationDate',
                    'citationCount',
                    'venue',
                ],
            )

            if not results or not results.items:
                return f"No papers found for query: '{query}'"

            # Format search results
            formatted_results = []
            for paper in results.items:
                formatted_result = self._format_paper(paper)
                if formatted_result:
                    formatted_results.append(formatted_result)

                # Stop when we have enough results
                if len(formatted_results) >= limit:
                    break

            if not formatted_results:
                return f"No valid papers found for query: '{query}'"

            return "\n\n" + "=" * 80 + "\n\n".join(formatted_results) + "\n\n" + "=" * 80

        except Exception as e:
            return (
                f"Error searching papers: {e}\n"
                f"Please try again later or with a different query."
            )

    def _format_paper(self, paper) -> Optional[str]:
        """
        Format a single paper result with all available metadata.

        Args:
            paper: A paper object from Semantic Scholar API

        Returns:
            A formatted string with paper metadata, or None if paper lacks essential info
        """
        # Extract basic information
        title = paper.title or "N/A"
        year = paper.year or "N/A"
        pub_date = paper.publicationDate or str(year)
        citation_count = paper.citationCount or 0
        venue = paper.venue or "N/A"

        # Extract external identifiers
        paper_id = paper.paperId or "N/A"
        arxiv_id = "N/A"
        doi = "N/A"

        if paper.externalIds and isinstance(paper.externalIds, dict):
            arxiv_id = paper.externalIds.get('ArXiv') or "N/A"
            doi = paper.externalIds.get('DOI') or "N/A"

        # Extract abstract (truncate if too long)
        abstract = paper.abstract or "N/A"
        if abstract != "N/A" and len(abstract) > 500:
            abstract = abstract[:500] + "..."

        # Extract authors
        authors_str = "N/A"
        if paper.authors:
            author_names = [a.name for a in paper.authors if a.name]
            if author_names:
                authors_str = ", ".join(author_names[:5])
                if len(author_names) > 5:
                    authors_str += f" et al. ({len(author_names)} total)"

        # Format output
        output = (
            f"Title: {title}\n"
            f"Authors: {authors_str}\n"
            f"Published: {pub_date} (Year: {year})\n"
            f"Venue: {venue}\n"
            f"Citation Count: {citation_count}\n"
            f"\n"
            f"Summary: {abstract}\n"
            f"\n"
            f"Identifiers:\n"
            f"  - Semantic Scholar ID: {paper_id}\n"
            f"  - arXiv ID: {arxiv_id}\n"
            f"  - DOI: {doi}"
        )

        return output

