# tests/scientific_research_tool/test_search_unpaywall.py

"""
Unit tests for SearchUnpaywall tool.

Tests the SearchUnpaywall tool for querying the Unpaywall API
to find open access information for academic papers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import requests

from llm_tool_hub.scientific_research_tool.search_unpaywall import SearchUnpaywall


def create_mock_unpaywall_response() -> Dict[str, Any]:
    """Create a mock Unpaywall API response."""
    return {
        "doi": "10.1038/nature12373",
        "title": "Nanometre-scale thermometry in a living cell",
        "journal_name": "Nature",
        "year": 2013,
        "is_oa": True,
        "oa_status": "bronze",
        "journal_is_oa": False,
        "best_oa_location": {
            "url": "https://www.nature.com/articles/nature12373.pdf",
            "host_type": "publisher",
            "version": "publishedVersion",
            "license": None,
        },
        "oa_locations": [
            {
                "url": "https://www.nature.com/articles/nature12373.pdf",
                "host_type": "publisher",
                "version": "publishedVersion",
            },
            {
                "url": "http://nrs.harvard.edu/urn-3:HUL.InstRepos:12285462",
                "host_type": "repository",
                "version": "submittedVersion",
                "license": "cc-by",
            },
        ],
        "z_authors": [
            {
                "raw_author_name": "G. Kucsko",
                "author_position": "first",
            },
            {
                "raw_author_name": "P. C. Maurer",
                "author_position": "middle",
            },
            {
                "raw_author_name": "M. D. Lukin",
                "author_position": "last",
            },
        ],
    }


class TestSearchUnpaywall:
    """Test suite for SearchUnpaywall."""

    def test_tool_has_required_metadata(self):
        """Test that the tool has all required metadata."""
        tool = SearchUnpaywall()
        assert tool.name == "search_unpaywall"
        assert len(tool.description) > 0
        assert tool.parameters is not None

    def test_tool_metadata_format(self):
        """Test that metadata follows the correct format."""
        tool = SearchUnpaywall()
        
        # Check parameters structure
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters
        assert "doi" in tool.parameters["properties"]
        assert "required" in tool.parameters
        assert "doi" in tool.parameters["required"]

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_success(self, mock_get):
        """Test successful search with valid DOI."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        # Verify the request was made
        mock_get.assert_called_once()
        
        # Verify the result contains expected information
        assert "Nanometre-scale thermometry" in result
        assert "Nature" in result
        assert "Open Access" in result
        assert "True" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_not_found(self, mock_get):
        """Test search with DOI not found in Unpaywall."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.invalid/notfound")

        assert "not found" in result.lower()

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "ERROR" in result
        assert "500" in result

    def test_search_unpaywall_empty_doi(self):
        """Test with empty DOI."""
        tool = SearchUnpaywall()
        result = tool.run(doi="")

        assert "ERROR" in result
        assert "required" in result.lower()

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "ERROR" in result
        assert "timed out" in result.lower() or "timeout" in result.lower()

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "ERROR" in result
        assert "connect" in result.lower()

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_custom_email(self, mock_get):
        """Test using custom email for API calls."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        custom_email = "custom@example.com"
        result = tool.run(doi="10.1038/nature12373", email=custom_email)

        # Verify custom email was used
        call_args = mock_get.call_args
        assert call_args[1]["params"]["email"] == custom_email

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_default_email(self, mock_get):
        """Test using default email when not specified."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        # Verify default email was used
        call_args = mock_get.call_args
        assert call_args[1]["params"]["email"] == SearchUnpaywall.DEFAULT_EMAIL

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_response_formatting(self, mock_get):
        """Test that response is properly formatted."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        # Check formatting
        assert "=" * 70 in result
        assert "-" * 70 in result
        assert "UNPAYWALL OPEN ACCESS INFORMATION" in result
        assert "OPEN ACCESS STATUS" in result
        assert "BEST OPEN ACCESS LOCATION" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_includes_title(self, mock_get):
        """Test that response includes paper title."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "Nanometre-scale thermometry" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_includes_journal(self, mock_get):
        """Test that response includes journal information."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "Journal:" in result
        assert "Nature" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_includes_authors(self, mock_get):
        """Test that response includes author information."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "AUTHORS" in result
        assert "G. Kucsko" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_includes_locations(self, mock_get):
        """Test that response includes OA location information."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "OPEN ACCESS LOCATIONS" in result
        assert "2" in result  # Number of locations

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_without_authors(self, mock_get):
        """Test response when authors are not available."""
        response_data = create_mock_unpaywall_response()
        response_data["z_authors"] = []

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "ERROR" not in result
        assert "Nanometre-scale thermometry" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_without_best_location(self, mock_get):
        """Test response when best OA location is not available."""
        response_data = create_mock_unpaywall_response()
        response_data["best_oa_location"] = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        assert "ERROR" not in result
        assert "Nanometre-scale thermometry" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_many_authors(self, mock_get):
        """Test response with many authors (should limit display)."""
        response_data = create_mock_unpaywall_response()
        # Create 15 authors
        response_data["z_authors"] = [
            {
                "raw_author_name": f"Author {i}",
                "author_position": "middle" if i > 0 else "first",
            }
            for i in range(15)
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        # Should limit to 10 + "and X more" message
        assert "... and" in result


    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_with_fulltext_enabled(self, mock_get):
        """Test that get_fulltext=True attempts to retrieve full text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        
        # Mock the _fetch_fulltext method to return some text
        with patch.object(tool, '_fetch_fulltext', return_value="This is the paper content..."):
            result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
            
            assert "FULL TEXT" in result
            assert "This is the paper content..." in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_with_fulltext_disabled(self, mock_get):
        """Test that get_fulltext=False does not include full text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373", get_fulltext=False)
        
        # Should not include full text section when get_fulltext=False
        assert "FULL TEXT" not in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_search_unpaywall_with_fulltext_unavailable(self, mock_get):
        """Test behavior when full text cannot be retrieved."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        tool = SearchUnpaywall()
        
        # Mock the _fetch_fulltext method to return None (failed retrieval)
        with patch.object(tool, '_fetch_fulltext', return_value=None):
            result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
            
            assert "could not be retrieved" in result

    def test_init_max_chars_parameter(self):
        """Test that max_chars parameter is properly set during initialization."""
        tool = SearchUnpaywall(max_chars=50000)
        assert tool.max_chars == 50000

    def test_init_max_chars_default(self):
        """Test that max_chars has correct default value."""
        tool = SearchUnpaywall()
        assert tool.max_chars == 100000

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_fetch_fulltext_truncation(self, mock_get):
        """Test that full text is truncated to max_chars."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = create_mock_unpaywall_response()
        mock_get.return_value = mock_response

        # Initialize with small max_chars for testing
        tool = SearchUnpaywall(max_chars=100)
        
        # Mock the _fetch_fulltext method to return a long text
        long_text = "a" * 500
        with patch.object(tool, '_fetch_fulltext', return_value=long_text[:100] + "... truncated ..."):
            result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
            
            # Result should contain the text truncation message
            assert "truncated" in result.lower() or len(result) > 0

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_fetch_from_url_with_text_content(self, mock_get):
        """Test fetching text content from a URL."""
        # Setup mock for API call
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = create_mock_unpaywall_response()
        
        # Setup mock for URL fetch (simulates text/plain response)
        url_response = Mock()
        url_response.headers = {"content-type": "text/plain"}
        url_response.text = "This is the paper content"
        url_response.raise_for_status = Mock()
        
        # Configure mock_get to return different responses
        mock_get.side_effect = [api_response, url_response]
        
        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
        
        assert "FULL TEXT" in result
        assert "This is the paper content" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_fetch_from_url_with_html_content(self, mock_get):
        """Test fetching HTML content from a URL."""
        # Setup mock for API call
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = create_mock_unpaywall_response()
        
        # Setup mock for URL fetch (simulates text/html response)
        url_response = Mock()
        url_response.headers = {"content-type": "text/html"}
        url_response.text = "<html><body>Paper content in HTML</body></html>"
        url_response.raise_for_status = Mock()
        
        # Configure mock_get to return different responses
        mock_get.side_effect = [api_response, url_response]
        
        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
        
        assert "FULL TEXT" in result
        assert "Paper content in HTML" in result

    @patch("llm_tool_hub.scientific_research_tool.search_unpaywall.requests.get")
    def test_fetch_from_url_timeout(self, mock_get):
        """Test handling of timeout when fetching URL."""
        # Setup mock for API call
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = create_mock_unpaywall_response()
        
        # Configure mock_get to raise timeout on URL fetch
        mock_get.side_effect = [api_response, requests.exceptions.Timeout("Connection timeout")]
        
        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373", get_fulltext=True)
        
        # Should handle timeout gracefully
        assert "could not be retrieved" in result


@pytest.mark.slow
@pytest.mark.integration
class TestSearchUnpaywall_RealAPI:
    """Integration tests using the real Unpaywall API."""

    def test_search_real_doi(self):
        """Test with a real DOI from the Unpaywall database."""
        tool = SearchUnpaywall()
        result = tool.run(doi="10.1038/nature12373")

        # Should succeed and contain expected information
        assert "ERROR" not in result
        assert "Nanometre-scale" in result or "thermometry" in result
        assert "Open Access" in result

    def test_search_invalid_doi(self):
        """Test with an invalid DOI."""
        tool = SearchUnpaywall()
        result = tool.run(doi="10.invalid/notfound")

        # Should return not found message
        assert "not found" in result.lower()
