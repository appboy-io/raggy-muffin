#!/usr/bin/env python3
"""
Test script for semantic context filtering
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/cleona_app/raggy-muffin/api')

from app.core.rag import (
    split_into_sections, 
    cosine_similarity,
    filter_context_by_semantic_relevance
)

# Test data - simulating mixed content chunks
test_chunk1 = """PROVIDER: Springfield Physical Therapy Center
DESCRIPTION: We offer comprehensive physical therapy services including post-surgical rehabilitation, sports injury recovery, and chronic pain management. Our licensed physical therapists use evidence-based techniques.
CATEGORIES: Healthcare, Physical Therapy, Rehabilitation
CONTACT INFORMATION:
Phone: (555) 123-4567
Email: info@springfieldpt.com
Website: https://www.springfieldpt.com
Address: 123 Main Street, Springfield, MA 01101

PROVIDER: Hope Counseling Services
DESCRIPTION: Professional mental health services including grief counseling, trauma therapy, and family counseling. Our compassionate therapists provide support for anxiety, depression, and life transitions.
CATEGORIES: Mental Health, Counseling, Therapy
CONTACT INFORMATION:
Phone: (555) 987-6543
Email: contact@hopecounseling.org
Website: https://www.hopecounseling.org
Address: 456 Oak Avenue, Springfield, MA 01102"""

test_chunk2 = """Services Available:
• Individual therapy sessions for adults and children
• Group therapy programs for addiction recovery
• Couples counseling and marriage therapy
• Specialized PTSD treatment programs
• Art therapy and creative expression workshops
• Mindfulness and meditation classes
• Crisis intervention services available 24/7
• Sliding scale fees based on income"""

async def test_section_splitting():
    """Test the section splitting functionality"""
    print("Testing section splitting...")
    sections = split_into_sections(test_chunk1)
    
    print(f"Found {len(sections)} sections from test chunk 1:")
    for i, section in enumerate(sections, 1):
        print(f"\nSection {i} ({len(section)} chars):")
        print(section[:150] + "..." if len(section) > 150 else section)
    
    # Test with bullet points
    sections2 = split_into_sections(test_chunk2)
    print(f"\n\nFound {len(sections2)} sections from test chunk 2:")
    for i, section in enumerate(sections2, 1):
        print(f"\nSection {i}:")
        print(section[:150] + "..." if len(section) > 150 else section)

def test_cosine_similarity():
    """Test cosine similarity calculation"""
    print("\nTesting cosine similarity...")
    
    # Test vectors
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]  # Same direction
    vec3 = [0.0, 1.0, 0.0]  # Orthogonal
    vec4 = [-1.0, 0.0, 0.0] # Opposite direction
    
    sim1 = cosine_similarity(vec1, vec2)
    sim2 = cosine_similarity(vec1, vec3)
    sim3 = cosine_similarity(vec1, vec4)
    
    print(f"Same vectors: {sim1:.3f} (expected ~1.0)")
    print(f"Orthogonal vectors: {sim2:.3f} (expected ~0.0)")
    print(f"Opposite vectors: {sim3:.3f} (expected ~-1.0)")

async def test_semantic_filtering():
    """Test the semantic relevance filtering"""
    print("\n\nTesting semantic filtering...")
    
    # Test queries
    queries = [
        "I need physical therapy for my knee injury",
        "I'm looking for grief counseling services",
        "What mental health services are available?",
        "I need help with sports injury recovery"
    ]
    
    chunks = [test_chunk1, test_chunk2]
    
    for query in queries:
        print(f"\n\nQuery: '{query}'")
        print("-" * 50)
        
        # Note: This will only work if the embedding service is available
        try:
            filtered_sections = await filter_context_by_semantic_relevance(
                query=query,
                chunks=chunks,
                threshold=0.2,  # Lower threshold for testing
                max_sections=3
            )
            
            print(f"Found {len(filtered_sections)} relevant sections:")
            for i, section in enumerate(filtered_sections, 1):
                print(f"\nRelevant Section {i}:")
                print(section[:200] + "..." if len(section) > 200 else section)
        except Exception as e:
            print(f"Note: Semantic filtering requires embedding service: {e}")
            print("Skipping semantic filter test...")
            break

async def main():
    """Run all tests"""
    print("=" * 60)
    print("SEMANTIC CONTEXT FILTERING TEST")
    print("=" * 60)
    
    # Test individual components
    await test_section_splitting()
    test_cosine_similarity()
    await test_semantic_filtering()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())