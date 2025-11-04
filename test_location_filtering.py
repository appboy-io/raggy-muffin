#!/usr/bin/env python3
"""
Test script to verify geographic filtering in RAG system
"""
import sys
import os
sys.path.insert(0, '/home/cleona_app/raggy-muffin/api')

from app.core.rag import extract_location_from_query, detect_locations_in_chunk, filter_chunks_by_location

def test_location_extraction():
    """Test extracting locations from queries"""
    test_queries = [
        "Our client is 10 weeks pregnant and lives in Spokane County. Can you list licensed midwives?",
        "Find clinics in Tacoma that accept Medicaid",
        "What services are available near Seattle?",
        "Resources in Pierce County for pregnant women",
        "Prenatal care options",  # No location
        "Housing assistance in Olympia, WA",
        "Mental health services around Bellevue"
    ]
    
    print("=" * 60)
    print("TESTING LOCATION EXTRACTION FROM QUERIES")
    print("=" * 60)
    
    for query in test_queries:
        locations = extract_location_from_query(query)
        print(f"\nQuery: {query[:60]}...")
        print(f"Extracted locations: {locations}")

def test_chunk_location_detection():
    """Test detecting locations in chunks"""
    test_chunks = [
        "County: Spokane\nCity: Spokane\nAddress: 123 Main St, Spokane, WA 99201",
        "Organization: Tacoma Medical Center\nLocation: Pierce County\nCity: Tacoma",
        "Physical Address: 3629 S. D St., Tacoma, WA 98418-6813",
        "Services provided statewide with no specific location",
        "County: Pierce\nCity: Tacoma\n Organization: MultiCare",
        "Address: 9040 Jackson Avenue, Spokane, WA"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING LOCATION DETECTION IN CHUNKS")
    print("=" * 60)
    
    for chunk in test_chunks:
        locations = detect_locations_in_chunk(chunk)
        print(f"\nChunk: {chunk[:80]}...")
        print(f"Detected locations: {locations}")

def test_filtering():
    """Test the filtering function"""
    chunks = [
        "County: Spokane\nServices: Midwifery\nAddress: 123 Main St, Spokane, WA",
        "County: Pierce\nCity: Tacoma\nServices: Prenatal care",
        "County: King\nCity: Seattle\nServices: Maternity ward",
        "County: Spokane\nCity: Spokane Valley\nServices: OB/GYN",
        "County: Pierce\nCity: Puyallup\nServices: Birth center"
    ]
    similarities = [0.8, 0.75, 0.7, 0.65, 0.6]
    
    print("\n" + "=" * 60)
    print("TESTING CHUNK FILTERING")
    print("=" * 60)
    
    # Test 1: Filter for Spokane
    print("\n--- Filtering for Spokane ---")
    filtered = filter_chunks_by_location(chunks, similarities, ["spokane"])
    print(f"Input: {len(chunks)} chunks")
    print(f"Output: {len(filtered)} chunks")
    for chunk, score in filtered:
        print(f"  Score {score:.2f}: {chunk[:50]}...")
    
    # Test 2: Filter for Pierce/Tacoma
    print("\n--- Filtering for Pierce County ---")
    filtered = filter_chunks_by_location(chunks, similarities, ["pierce"])
    print(f"Input: {len(chunks)} chunks")
    print(f"Output: {len(filtered)} chunks")
    for chunk, score in filtered:
        print(f"  Score {score:.2f}: {chunk[:50]}...")
    
    # Test 3: No location filter
    print("\n--- No location filter ---")
    filtered = filter_chunks_by_location(chunks, similarities, [])
    print(f"Input: {len(chunks)} chunks")
    print(f"Output: {len(filtered)} chunks")

if __name__ == "__main__":
    test_location_extraction()
    test_chunk_location_detection()
    test_filtering()
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)