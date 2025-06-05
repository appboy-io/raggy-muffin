from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re
from categories import category_manager, normalize_categories

class LLMDataExtractor:
    def __init__(self, model_name="Locutusque/TinyMistral-248M"):
        """Initialize the LLM-based data extractor with lightweight model"""
        self.device = "cpu"  # Use CPU to avoid CUDA issues
        
        try:
            print(f"Loading TinyMistral-248M model on {self.device}...")
            
            # Load tokenizer and model separately for better control
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="auto"
            )
            
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                # Remove device argument when using accelerate
                max_length=512,
                truncation=True,
                do_sample=True,
                temperature=0.1,
                top_p=0.9
            )
            print("TinyMistral-248M model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading TinyMistral model: {e}")
            print("Using fallback model...")
            # Fallback to simpler model
            self.generator = pipeline("text-generation", model="gpt2", device=-1, max_length=256)
    
    def extract_structured_data(self, text, file_type="text"):
        """
        Extract structured data using LLM prompting
        Returns same format as original extraction.py for compatibility
        """
        # Create extraction prompt based on file type
        prompt = self._create_extraction_prompt(text, file_type)
        
        # Generate extraction using LLM
        try:
            response = self.generator(
                prompt,
                max_new_tokens=200,
                num_return_sequences=1,
                temperature=0.3,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id if hasattr(self, 'tokenizer') else None
            )
            
            extracted_text = response[0]['generated_text'][len(prompt):].strip()
            
            # Parse the LLM response into structured format
            parsed_data = self._parse_llm_response(extracted_text, text)
            
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            # Fallback to basic extraction
            parsed_data = self._fallback_extraction(text)
        
        return parsed_data
    
    def _create_extraction_prompt(self, text, file_type):
        """Create a detailed extraction prompt optimized for Zephyr-7B-beta's chat format"""
        
        # Get available categories for the prompt
        available_categories = category_manager.get_all_categories()
        categories_str = ", ".join(available_categories[:10])  # Limit for token count
        
        prompt = f"""<|system|>
You are an expert data extraction assistant. Extract structured information from documents and return valid JSON.
</s>
<|user|>
Extract structured information from this {file_type} document and return it as valid JSON.

EXTRACTION REQUIREMENTS:
1. PROVIDER NAME: Extract the organization/provider name (company, nonprofit, agency, etc.)
2. CATEGORIES: Identify aid/service categories from this list: {categories_str}
3. CONTACTS: Find all emails, phone numbers, websites, and addresses  
4. DESCRIPTION: Write a concise summary of the main services or assistance offered

DOCUMENT CONTENT:
{text[:1200]}

Return your response as a valid JSON object with this exact structure:
{{
    "provider_name": "Name of the organization or provider",
    "categories": ["category1", "category2"],
    "emails": ["email1@example.com"],
    "phones": ["123-456-7890"],
    "urls": ["https://website.com"],
    "addresses": ["123 Main St"],
    "description": "Brief description of services"
}}

Only include categories that actually match the provided list. Ensure all contact information is accurately extracted.
Extract the provider name from headers, titles, or organization mentions in the document.
</s>
<|assistant|>
"""
        return prompt
    
    def _parse_llm_response(self, llm_response, original_text):
        """Parse LLM response into the expected data structure"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_json = json.loads(json_str)
                
                # Convert to expected format
                categories = {}
                if 'categories' in parsed_json:
                    for cat in parsed_json['categories']:
                        # Use category manager for normalization
                        norm_cat, confidence = category_manager.normalize_category(cat, threshold=0.6)
                        if norm_cat:
                            categories[norm_cat] = [cat]
                
                contacts = {
                    "emails": parsed_json.get('emails', []),
                    "phones": parsed_json.get('phones', []),
                    "urls": parsed_json.get('urls', []),
                    "addresses": parsed_json.get('addresses', [])
                }
                
                description = parsed_json.get('description', '')
                provider_name = parsed_json.get('provider_name', '')
                
                return {
                    "provider_name": provider_name,
                    "categories": categories,
                    "contacts": contacts,
                    "description": description
                }
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
        
        # If parsing fails, fall back to basic extraction
        return self._fallback_extraction(original_text)
    
    def _fallback_extraction(self, text):
        """Fallback to basic pattern-based extraction if LLM fails"""
        # Basic regex patterns
        EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        PHONE_PATTERN = r'\b(\(\d{3}\)\s*|\d{3}[-.])\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        
        contacts = {
            "emails": re.findall(EMAIL_PATTERN, text, re.IGNORECASE),
            "phones": re.findall(PHONE_PATTERN, text),
            "urls": re.findall(URL_PATTERN, text),
            "addresses": []
        }
        
        # Basic category detection using keywords
        categories = {}
        text_lower = text.lower()
        basic_categories = {
            "food": ["food", "meal", "grocery", "kitchen", "restaurant"],
            "housing": ["housing", "shelter", "apartment", "home", "rent"],
            "healthcare": ["health", "medical", "doctor", "clinic", "hospital"],
            "employment": ["job", "work", "employment", "career", "hiring"]
        }
        
        for category, keywords in basic_categories.items():
            found_terms = [kw for kw in keywords if kw in text_lower]
            if found_terms:
                categories[category] = found_terms
        
        # Extract first few sentences as description
        sentences = text.split('.')[:3]
        description = '. '.join(sentences).strip()
        
        # Try to extract provider name from text
        provider_name = extract_provider_name_fallback(text)
        
        return {
            "provider_name": provider_name,
            "categories": categories,
            "contacts": contacts,
            "description": description
        }

def extract_provider_name_fallback(text):
    """Fallback method to extract provider name using patterns"""
    lines = text.split('\n')
    
    # Look for common provider name patterns
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
            
        # Look for organization indicators
        org_patterns = [
            r'^([A-Z][A-Za-z\s&,.-]+(?:Inc\.?|LLC|Corp\.?|Foundation|Center|Agency|Services|Association|Organization))',
            r'^([A-Z][A-Za-z\s&,.-]{5,50})\s*$',  # Title case lines (likely org names)
            r'Organization[:\s]+([A-Za-z\s&,.-]+)',
            r'Provider[:\s]+([A-Za-z\s&,.-]+)',
            r'Agency[:\s]+([A-Za-z\s&,.-]+)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 100:  # Reasonable length
                    return name
    
    # If no pattern matches, try first meaningful line
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 10 and len(line) < 80:
            # Skip lines that look like categories or contact info
            if not any(skip in line.lower() for skip in ['email', 'phone', 'address', 'website', 'http']):
                return line
    
    return ""

# File type specific extractors
class PDFLLMExtractor(LLMDataExtractor):
    """LLM extractor specialized for PDF documents"""
    
    def extract_structured_data(self, text, file_type="PDF"):
        return super().extract_structured_data(text, file_type)

class CSVLLMExtractor(LLMDataExtractor):
    """LLM extractor specialized for CSV data"""
    
    def extract_structured_data(self, text, file_type="CSV"):
        # For CSV, we might want to handle structured data differently
        return super().extract_structured_data(text, file_type)

class ExcelLLMExtractor(LLMDataExtractor):
    """LLM extractor for Excel files"""
    
    def extract_structured_data(self, text, file_type="Excel"):
        return super().extract_structured_data(text, file_type)

class TextLLMExtractor(LLMDataExtractor):
    """LLM extractor for plain text files"""
    
    def extract_structured_data(self, text, file_type="Text"):
        return super().extract_structured_data(text, file_type)

# Factory function to get the appropriate extractor
def get_llm_extractor(file_type):
    """Factory function to get the appropriate LLM extractor"""
    extractors = {
        "pdf": PDFLLMExtractor,
        "csv": CSVLLMExtractor,
        "excel": ExcelLLMExtractor,
        "txt": TextLLMExtractor,
        "text": TextLLMExtractor
    }
    
    extractor_class = extractors.get(file_type.lower(), LLMDataExtractor)
    return extractor_class()

# Convenience function for backward compatibility
def extract_structured_data_llm(text, file_type="text"):
    """
    Main function to extract structured data using LLM
    Maintains compatibility with existing extraction.py interface
    """
    extractor = get_llm_extractor(file_type)
    return extractor.extract_structured_data(text, file_type)