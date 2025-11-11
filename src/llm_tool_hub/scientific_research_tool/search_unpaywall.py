# src/llm_tool_hub/scientific_research_tool/search_unpaywall.py

"""
Search Unpaywall API for Open Access Information and Full Text

Unpaywall provides a database of free scholarly articles.
This tool queries the Unpaywall API to find open access information and full text
for papers by DOI.

API Documentation: https://unpaywall.org/products/api
"""

import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from ..base_tool import BaseTool


class SearchUnpaywall(BaseTool):
    """
    Search for open access information using Unpaywall API and retrieve full text.
    
    Unpaywall is a database of free scholarly articles. It provides information about
    whether a paper is openly accessible and where to find it.
    
    This tool queries the Unpaywall API to retrieve open access status and location
    information for academic papers by DOI. It can also attempt to retrieve the full
    text of the paper from the best available OA location.
    """

    # Required metadata
    name: str = "search_unpaywall"
    description: str = (
        "Search for open access information using Unpaywall API and optionally retrieve full text. "
        "Takes a DOI (Digital Object Identifier) and returns open access status, "
        "available copies, and access links. "
        "If get_fulltext=true, attempts to retrieve the full paper text from the OA location. "
        "Returns formatted information about paper metadata and optionally the full text "
        "if available and within the character limit."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "doi": {
                "type": "string",
                "description": (
                    "Digital Object Identifier (DOI) of the paper to search for. "
                    "Examples: '10.1038/nature12373', '10.1016/j.cell.2013.02.022'. "
                    "Must be a valid DOI."
                ),
            },
            "email": {
                "type": "string",
                "description": (
                    "Email address for API calls (required by Unpaywall). "
                    "This is used for rate limiting and contact purposes. "
                    "Defaults to the configured default email if not provided."
                ),
            },
            "get_fulltext": {
                "type": "boolean",
                "description": (
                    "If true, attempts to retrieve the full text of the paper. "
                    "Default is False. Full text will be truncated to max_chars."
                ),
                "default": False,
            },
        },
        "required": ["doi"],
    }

    # Default email for Unpaywall API
    DEFAULT_EMAIL = "zc18202534657@gmail.com"
    API_BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, max_chars: int = 100000, **kwargs):
        """
        Initialize the SearchUnpaywall tool.

        Args:
            max_chars: Maximum number of characters to retrieve for full text (default: 100000)
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(**kwargs)
        self.max_chars = max_chars
        logger.info(f"SearchUnpaywall initialized with max_chars={max_chars}")

    def run(self, doi: str, email: Optional[str] = None, get_fulltext: bool = False) -> str:
        """
        Query Unpaywall API for open access information and optionally retrieve full text.

        Args:
            doi: Digital Object Identifier of the paper
            email: Email address for API calls (optional, uses default if not provided)
            get_fulltext: If True, attempt to retrieve full text of the paper

        Returns:
            Formatted string containing open access information and optionally full text
        """
        if not doi:
            return "ERROR: DOI is required"

        # Use provided email or default
        email_to_use = email or self.DEFAULT_EMAIL

        try:
            # Query the Unpaywall API
            url = f"{self.API_BASE_URL}/{doi}"
            params = {"email": email_to_use}

            logger.info(f"Searching Unpaywall for DOI: {doi}")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 404:
                return f"Paper with DOI '{doi}' not found in Unpaywall database"

            if response.status_code != 200:
                return (
                    f"ERROR: Unpaywall API returned status code {response.status_code}. "
                    f"Message: {response.text[:200]}"
                )

            # Parse the response
            data = response.json()
            result = self._format_unpaywall_result(data)

            # Attempt to retrieve full text if requested
            if get_fulltext:
                fulltext = self._fetch_fulltext(data)
                if fulltext:
                    result += "\n\n" + "=" * 70 + "\n"
                    result += "FULL TEXT\n"
                    result += "=" * 70 + "\n"
                    result += fulltext
                else:
                    result += "\n\nNOTE: Full text could not be retrieved from available OA locations."

            return result

        except requests.exceptions.Timeout:
            return "ERROR: Request to Unpaywall API timed out"
        except requests.exceptions.ConnectionError:
            return "ERROR: Failed to connect to Unpaywall API"
        except requests.exceptions.RequestException as e:
            return f"ERROR: Request failed - {str(e)[:200]}"
        except Exception as e:
            logger.error(f"Error searching Unpaywall: {str(e)}")
            return f"ERROR: Unexpected error - {str(e)[:200]}"

    def _fetch_fulltext(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Attempt to retrieve the full text of a paper from available OA locations.

        Args:
            data: Response data from Unpaywall API

        Returns:
            Full text of the paper (truncated to max_chars) or None if unavailable
        """
        # Get list of OA locations to try
        locations_to_try = []

        # First priority: best_oa_location
        if data.get("best_oa_location") and data["best_oa_location"].get("url"):
            locations_to_try.append(data["best_oa_location"]["url"])

        # Second priority: other oa_locations
        if data.get("oa_locations"):
            for loc in data["oa_locations"]:
                if loc.get("url") and loc["url"] not in locations_to_try:
                    locations_to_try.append(loc["url"])

        # Try to fetch from each location
        for url in locations_to_try:
            try:
                logger.info(f"Attempting to fetch full text from: {url}")
                text = self._fetch_from_url(url)
                if text:
                    # Truncate to max_chars if needed
                    if len(text) > self.max_chars:
                        text = text[: self.max_chars] + f"\n\n[... text truncated at {self.max_chars} characters ...]"
                    return text
            except Exception as e:
                logger.debug(f"Failed to fetch from {url}: {str(e)}")
                continue

        return None

    def _fetch_from_url(self, url: str) -> Optional[str]:
        """
        Fetch text content from a given URL.

        Args:
            url: URL to fetch from

        Returns:
            Text content or None if unable to extract text
        """
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            # Try to extract text based on content type
            content_type = response.headers.get("content-type", "").lower()

            if "text/plain" in content_type or "text/html" in content_type:
                # For plain text or HTML, return the text
                return response.text

            elif "application/pdf" in content_type:
                # For PDF, try to extract text
                return self._extract_text_from_pdf(response.content)

            else:
                # For other content types, try to return text if available
                try:
                    return response.text
                except Exception:
                    return None

        except requests.exceptions.Timeout:
            logger.debug(f"Timeout fetching from {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request exception fetching from {url}: {str(e)}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching from {url}: {str(e)}")
            return None

    def _extract_text_from_pdf(self, content: bytes) -> Optional[str]:
        """
        Extract text from PDF content.

        This is a simplified version that attempts to extract ASCII text from PDF.
        For full PDF text extraction, consider using PyPDF2 or pdfplumber libraries.

        Args:
            content: PDF file content as bytes

        Returns:
            Extracted text or None if unable to extract
        """
        try:
            # Simple text extraction from PDF: look for readable ASCII text
            # This is a basic implementation that works for many PDFs
            text = ""
            for byte in content:
                # Include printable ASCII characters and common symbols
                if 32 <= byte <= 126 or byte in (9, 10, 13):  # space to ~, tab, newline, carriage return
                    text += chr(byte)
                elif byte >= 128:
                    # Skip high bytes (binary PDF data)
                    continue

            # Clean up the text
            text = text.strip()
            if text and len(text) > 100:  # Only return if we extracted reasonable amount of text
                return text

            return None

        except Exception as e:
            logger.debug(f"Error extracting PDF text: {str(e)}")
            return None

    def _format_unpaywall_result(self, data: Dict[str, Any]) -> str:
        """
        Format the Unpaywall API response into a readable string.

        Args:
            data: Response data from Unpaywall API

        Returns:
            Formatted result string
        """
        result_lines = []
        result_lines.append("=" * 70)
        result_lines.append("UNPAYWALL OPEN ACCESS INFORMATION")
        result_lines.append("=" * 70)

        # Basic information
        if "title" in data:
            result_lines.append(f"\nTitle: {data['title']}")

        if "doi" in data:
            result_lines.append(f"DOI: {data['doi']}")

        if "journal_name" in data:
            result_lines.append(f"Journal: {data['journal_name']}")

        if "year" in data:
            result_lines.append(f"Year: {data['year']}")

        # Open Access Status
        result_lines.append("\n" + "-" * 70)
        result_lines.append("OPEN ACCESS STATUS")
        result_lines.append("-" * 70)

        is_oa = data.get("is_oa", False)
        oa_status = data.get("oa_status", "unknown")
        result_lines.append(f"Is Open Access: {is_oa}")
        if oa_status:
            result_lines.append(f"OA Status: {oa_status}")

        # Journal information
        journal_is_oa = data.get("journal_is_oa", False)
        if journal_is_oa:
            result_lines.append("Journal is fully open access: Yes")

        # Best OA Location
        if "best_oa_location" in data and data["best_oa_location"]:
            result_lines.append("\n" + "-" * 70)
            result_lines.append("BEST OPEN ACCESS LOCATION")
            result_lines.append("-" * 70)
            best_loc = data["best_oa_location"]

            if "url" in best_loc:
                result_lines.append(f"URL: {best_loc['url']}")
            if "host_type" in best_loc:
                result_lines.append(f"Host Type: {best_loc['host_type']}")
            if "version" in best_loc:
                result_lines.append(f"Version: {best_loc['version']}")
            if "license" in best_loc and best_loc["license"]:
                result_lines.append(f"License: {best_loc['license']}")

        # All OA Locations
        oa_locations = data.get("oa_locations", [])
        if oa_locations:
            result_lines.append("\n" + "-" * 70)
            result_lines.append("ALL OPEN ACCESS LOCATIONS")
            result_lines.append("-" * 70)
            for i, loc in enumerate(oa_locations, 1):
                result_lines.append(f"\nLocation {i}:")
                if "url" in loc:
                    result_lines.append(f"  URL: {loc['url']}")
                if "host_type" in loc:
                    result_lines.append(f"  Host Type: {loc['host_type']}")
                if "version" in loc:
                    result_lines.append(f"  Version: {loc['version']}")
                if "license" in loc and loc["license"]:
                    result_lines.append(f"  License: {loc['license']}")

        # Additional metadata
        result_lines.append("\n" + "-" * 70)
        result_lines.append("ADDITIONAL INFORMATION")
        result_lines.append("-" * 70)

        if "published_date" in data:
            result_lines.append(f"Published Date: {data['published_date']}")

        # Handle authors from z_authors or authors field
        if "z_authors" in data and data["z_authors"]:
            author_names = [author.get("raw_author_name", "") for author in data["z_authors"]]
            author_names = [name for name in author_names if name]  # Filter empty names
            if author_names:
                authors_str = ", ".join(author_names[:5])
                if len(author_names) > 5:
                    authors_str += f", ... and {len(author_names) - 5} more"
                result_lines.append(f"AUTHORS: {authors_str}")
        elif "authors" in data and data["authors"]:
            authors_str = ", ".join(data["authors"][:5])
            if len(data["authors"]) > 5:
                authors_str += f", ... and {len(data['authors']) - 5} more"
            result_lines.append(f"AUTHORS: {authors_str}")

        result_lines.append("\n" + "=" * 70)

        return "\n".join(result_lines)
