#!/usr/bin/env python3
"""
Test the location extraction function
"""
import sys
import os
sys.path.insert(0, '/home/cleona_app/raggy-muffin/api')

from app.core.rag import extract_location_from_query

def test_location_extraction():
    test_queries = [
        "This client asked for a midwife who supports VBAC/TOLAC in Eastern Washington. Which providers meet that criteria?",
        "Find providers in Spokane County",
        "Looking for services in Tacoma",
        "Resources near Seattle",
        "in Pierce County",
        "in Eastern Washington"
    ]
    
    print("Testing location extraction:")
    for query in test_queries:
        locations = extract_location_from_query(query)
        print(f"Query: {query}")
        print(f"Extracted: {locations}")
        print()

if __name__ == "__main__":
    test_location_extraction()