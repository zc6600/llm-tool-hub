#!/usr/bin/env python3
# draft/explore_unpaywall_api.py

"""
Explore Unpaywall API to understand its format and usage.

Unpaywall is a database of free scholarly articles.
API Documentation: https://unpaywall.org/products/api

Usage:
- Query by DOI: https://api.unpaywall.org/v2/{DOI}?email={email}
- Returns: Open access information for academic papers
"""

import requests
import json

# Example DOI for testing
TEST_DOI = "10.1038/nature12373"
EMAIL = "zc18202534657@gmail.com"  # Required by Unpaywall API

def test_unpaywall_api():
    """Test the Unpaywall API with a sample DOI."""
    
    print("=" * 70)
    print("Testing Unpaywall API")
    print("=" * 70)
    
    # Construct the URL
    url = f"https://api.unpaywall.org/v2/{TEST_DOI}"
    params = {"email": EMAIL}
    
    print(f"\nAPI Endpoint: {url}")
    print(f"Parameters: {params}")
    
    try:
        # Make the request
        print("\nMaking request...")
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 70)
            print("API Response Structure:")
            print("=" * 70)
            print(json.dumps(data, indent=2))
            
            # Highlight key fields
            print("\n" + "=" * 70)
            print("Key Fields:")
            print("=" * 70)
            if "title" in data:
                print(f"Title: {data['title']}")
            if "doi" in data:
                print(f"DOI: {data['doi']}")
            if "is_oa" in data:
                print(f"Is Open Access: {data['is_oa']}")
            if "best_oa_location" in data:
                print(f"Best OA Location: {data['best_oa_location']}")
            if "oa_locations" in data:
                print(f"Number of OA Locations: {len(data['oa_locations'])}")
            if "authors" in data:
                print(f"Authors: {data['authors']}")
            if "year" in data:
                print(f"Publication Year: {data['year']}")
            if "journal_name" in data:
                print(f"Journal: {data['journal_name']}")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")


def test_unpaywall_invalid_doi():
    """Test with an invalid DOI to see error response."""
    
    print("\n" + "=" * 70)
    print("Testing with Invalid DOI")
    print("=" * 70)
    
    url = f"https://api.unpaywall.org/v2/invalid-doi"
    params = {"email": EMAIL}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


def test_multiple_dois():
    """Test with multiple DOIs to understand response patterns."""
    
    dois = [
        "10.1038/nature12373",      # Nature paper
        "10.1016/j.cell.2013.02.022",  # Cell paper
        "10.1145/2783446.2807897",   # Conference paper
    ]
    
    print("\n" + "=" * 70)
    print("Testing Multiple DOIs")
    print("=" * 70)
    
    for doi in dois:
        print(f"\nTesting DOI: {doi}")
        url = f"https://api.unpaywall.org/v2/{doi}"
        params = {"email": EMAIL}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  Title: {data.get('title', 'N/A')[:60]}...")
                print(f"  Is OA: {data.get('is_oa', False)}")
                print(f"  Year: {data.get('year', 'N/A')}")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    print("Unpaywall API Exploration\n")
    
    test_unpaywall_api()
    test_unpaywall_invalid_doi()
    test_multiple_dois()
    
    print("\n" + "=" * 70)
    print("Exploration Complete")
    print("=" * 70)
    print("\nKey Observations:")
    print("1. Unpaywall API requires an email parameter")
    print("2. It returns comprehensive OA information for papers")
    print("3. Main query parameter: DOI")
    print("4. No API key required (but email is)")
    print("5. Response includes title, authors, year, journal, OA locations, etc.")
