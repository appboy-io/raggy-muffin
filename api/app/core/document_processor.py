import pdfplumber
import pandas as pd
import io
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

async def process_document(
    file_content: bytes, 
    filename: str, 
    file_type: str
) -> Dict[str, Any]:
    """
    Process uploaded document and extract text
    """
    try:
        if file_type.upper() == "PDF":
            text = await extract_pdf_text(file_content)
        elif file_type.upper() == "CSV":
            text = await extract_csv_text(file_content)
        elif file_type.upper() in ["XLSX", "XLS", "EXCEL"]:
            text = await extract_excel_text(file_content)
        elif file_type.upper() in ["TXT", "TEXT", "MD", "RST"]:
            text = await extract_text_file(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        word_count = len(text.split()) if text else 0
        
        return {
            "success": True,
            "text": text,
            "word_count": word_count,
            "filename": filename,
            "file_type": file_type
        }
        
    except Exception as e:
        logger.error(f"Error processing document {filename}: {e}")
        return {
            "success": False,
            "error": str(e),
            "filename": filename,
            "file_type": file_type
        }

async def extract_pdf_text(file_content: bytes) -> str:
    """Extract text from a PDF file"""
    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        return full_text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise

async def extract_csv_text(file_content: bytes) -> str:
    """Extract and format text from a CSV file"""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a text representation of each row
            chunk = ""
            for col in df.columns:
                if pd.notna(row[col]):
                    chunk += f"{col}: {row[col]}\n"
            text_chunks.append(chunk)
            
        return "\n\n".join(text_chunks)
    except Exception as e:
        logger.error(f"Error extracting CSV text: {e}")
        raise

async def extract_excel_text(file_content: bytes) -> str:
    """Extract and format text from an Excel file"""
    try:
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a text representation of each row
            chunk = ""
            for col in df.columns:
                if pd.notna(row[col]):
                    chunk += f"{col}: {row[col]}\n"
            text_chunks.append(chunk)
            
        return "\n\n".join(text_chunks)
    except Exception as e:
        logger.error(f"Error extracting Excel text: {e}")
        raise

async def extract_text_file(file_content: bytes) -> str:
    """Extract text from a plain text file"""
    try:
        # Try to decode as UTF-8, fallback to other encodings
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # If all else fails, decode with errors='replace'
            return file_content.decode('utf-8', errors='replace')
            
    except Exception as e:
        logger.error(f"Error extracting text file: {e}")
        raise

def validate_file_size(file_size: int, max_size_mb: int) -> bool:
    """Validate file size against limit"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def get_file_type_from_filename(filename: str) -> Optional[str]:
    """Extract file type from filename"""
    if '.' not in filename:
        return None
    
    extension = filename.split('.')[-1].lower()
    
    type_mapping = {
        'pdf': 'PDF',
        'csv': 'CSV',
        'xlsx': 'Excel',
        'xls': 'Excel',
        'txt': 'Text',
        'md': 'Text',
        'rst': 'Text'
    }
    
    return type_mapping.get(extension)