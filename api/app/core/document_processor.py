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
        
        # Clean up column names - remove "Unnamed:" columns
        cleaned_columns = []
        for col in df.columns:
            if isinstance(col, str) and col.startswith('Unnamed:'):
                # Skip unnamed columns or give them a better name based on position
                continue
            cleaned_columns.append(col)
        
        # Only keep columns that have actual names
        if cleaned_columns:
            df = df[cleaned_columns]
        
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a text representation of each row
            chunk = ""
            for col in df.columns:
                # Skip columns that are "Unnamed"
                if isinstance(col, str) and col.startswith('Unnamed:'):
                    continue
                if pd.notna(row[col]):
                    # Clean the value to remove any "Unnamed:" references
                    value = str(row[col])
                    if 'Unnamed:' not in value:
                        chunk += f"{col}: {value}\n"
            if chunk.strip():  # Only add non-empty chunks
                text_chunks.append(chunk)
            
        return "\n\n".join(text_chunks)
    except Exception as e:
        logger.error(f"Error extracting CSV text: {e}")
        raise

async def extract_excel_text(file_content: bytes) -> str:
    """Extract and format text from an Excel file with intelligent content categorization"""
    import re
    
    def categorize_content(value: str) -> str:
        """Categorize content based on patterns"""
        if pd.isna(value) or not str(value).strip():
            return None
            
        value_str = str(value).strip()
        
        # Email pattern
        if '@' in value_str and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
            return f"Email: {value_str}"
        
        # Phone pattern (various formats)
        phone_pattern = r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$|^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$'
        if re.match(phone_pattern, value_str.replace(' ', '')):
            return f"Phone: {value_str}"
        
        # Website/URL pattern
        if value_str.startswith(('http://', 'https://', 'www.')) or '.com' in value_str or '.org' in value_str:
            # Clean up malformed URLs with dots
            value_str = re.sub(r'\.\s+', '.', value_str)  # Fix ". " to "."
            value_str = re.sub(r'\.{2,}', '.', value_str)  # Fix ".." to "."
            return f"Website: {value_str}"
        
        # Address pattern (contains street numbers and typical address keywords)
        address_keywords = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 
                          'blvd', 'boulevard', 'suite', 'ste', 'apt', 'floor', 'fl']
        has_number = bool(re.search(r'\d+', value_str))
        has_address_word = any(word in value_str.lower() for word in address_keywords)
        # Also check for state abbreviations
        has_state = bool(re.search(r'\b[A-Z]{2}\b\s*\d{5}', value_str))  # State + ZIP
        
        if has_number and (has_address_word or has_state):
            return f"Address: {value_str}"
        
        # Date pattern
        if re.match(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}', value_str):
            return f"Date: {value_str}"
        
        # If it's a proper name (heuristic: starts with capital, contains spaces)
        if len(value_str) > 3 and value_str[0].isupper() and ' ' in value_str and not any(char.isdigit() for char in value_str):
            # Check if it might be a provider name with credentials
            if any(cred in value_str.upper() for cred in ['LM', 'CPM', 'MD', 'DO', 'NP', 'PA', 'RN', 'MSN', 'PHD', 'ND', 'CNM']):
                return f"Provider: {value_str}"
            # Check if it's an organization name
            elif any(org_word in value_str.lower() for org_word in ['clinic', 'center', 'hospital', 'health', 'medical', 'midwifery', 'birth']):
                return f"Organization: {value_str}"
        
        # Default - return with the column name if available
        return value_str
    
    try:
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
        text_chunks = []
        
        for _, row in df.iterrows():
            # Create a structured representation of each row
            chunk_parts = []
            provider_name = None
            organization = None
            contact_info = []
            other_info = []
            
            for col in df.columns:
                if pd.notna(row[col]):
                    value = str(row[col]).strip()
                    if not value or value.lower() == 'nan':
                        continue
                    
                    # Categorize the content
                    categorized = categorize_content(value)
                    
                    if categorized:
                        if categorized.startswith('Provider:'):
                            provider_name = categorized
                        elif categorized.startswith('Organization:'):
                            organization = categorized
                        elif categorized.startswith(('Phone:', 'Email:', 'Website:', 'Address:')):
                            contact_info.append(categorized)
                        else:
                            # For named columns, include the column name
                            if not isinstance(col, str) or not col.startswith('Unnamed:'):
                                other_info.append(f"{col}: {categorized}")
                            else:
                                # For unnamed columns, just use the categorized content
                                if categorized not in ['Date:', 'Click here!']:  # Skip common unhelpful values
                                    other_info.append(categorized)
            
            # Build the chunk in a structured way
            if provider_name or organization or contact_info or other_info:
                chunk = ""
                if provider_name:
                    chunk += f"{provider_name}\n"
                if organization:
                    chunk += f"{organization}\n"
                if contact_info:
                    chunk += "CONTACT INFORMATION:\n"
                    for info in contact_info:
                        chunk += f"  {info}\n"
                if other_info:
                    for info in other_info:
                        chunk += f"{info}\n"
                
                if chunk.strip():
                    text_chunks.append(chunk.strip())
        
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