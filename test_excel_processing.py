#!/usr/bin/env python3
"""
Test script to demonstrate the new Excel processing capabilities
"""
import asyncio
import sys
import pandas as pd
import io
from pathlib import Path

# Add the api directory to Python path
api_path = Path(__file__).parent / "api"
sys.path.insert(0, str(api_path))

from app.core.document_processor import extract_excel_text

async def test_excel_processing():
    """Test the new Excel processing with sample data"""
    
    # Create sample data that matches Kate Wild's format
    sample_data = {
        'Name': ['Kate Wild LM, CPM, Susan Lawler LM CPM'],
        'Unnamed: 1': ['All About Birth Midwifery'],
        'Unnamed: 2': ['2025-04-16 00:00:00'],
        'Unnamed: 3': ['Pierce'],
        'Unnamed: 4': ['Pierce'], 
        'Unnamed: 5': ['6002 Westgate Blvd suite 120 Tacoma, WA 98406'],
        'Unnamed: 6': ['Tacoma'],
        'Unnamed: 7': ['(253) 761-8939'],
        'Unnamed: 8': [''],
        'Unnamed: 9': [''],
        'Unnamed: 10': ['https://allaboutbirthmidwifery.com/'],
        'Unnamed: 11': ['Midwifery Care with birth center birth at Tacoma Birthing Inn']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Convert to Excel bytes
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_bytes = excel_buffer.getvalue()
    
    print("Testing new Excel processor with Kate Wild's data...")
    print("=" * 60)
    
    # Process with new logic
    try:
        result = await extract_excel_text(excel_bytes)
        print("PROCESSED OUTPUT:")
        print(result)
        print("=" * 60)
        
        # Check if contact information is properly extracted
        if "CONTACT INFORMATION:" in result:
            print("✓ SUCCESS: Contact information section found!")
        else:
            print("✗ ERROR: Contact information section not found")
            
        if "Phone: (253) 761-8939" in result:
            print("✓ SUCCESS: Phone number properly categorized!")
        else:
            print("✗ ERROR: Phone number not found or incorrectly categorized")
            
        if "Website: https://allaboutbirthmidwifery.com/" in result:
            print("✓ SUCCESS: Website properly categorized!")
        else:
            print("✗ ERROR: Website not found or incorrectly categorized")
            
        if "Address: 6002 Westgate Blvd suite 120 Tacoma, WA 98406" in result:
            print("✓ SUCCESS: Address properly categorized!")
        else:
            print("✗ ERROR: Address not found or incorrectly categorized")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_excel_processing())