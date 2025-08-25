import ollama
import json
import re
import os
from categories import category_manager, normalize_categories

class LLMDataExtractor:
    def __init__(self):
        """Initialize the LLM-based data extractor using Ollama"""
        self.model = os.getenv('OLLAMA_CHAT_MODEL', 'llama3.2:3b-instruct-q4_0')
        self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        print(f"Using Ollama model: {self.model}")
    
    def extract_structured_data(self, text, file_type="text"):
        """
        Extract structured data using LLM prompting
        Returns same format as original extraction.py for compatibility
        """
        # Create extraction prompt based on file type
        prompt = self._create_extraction_prompt(text, file_type)
        
        # Generate extraction using LLM
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': 'You are an expert data extraction assistant. Extract structured information from documents and return valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                options={'host': self.host, 'temperature': 0.3}
            )
            
            extracted_text = response['message']['content']
            
            # Parse the LLM response into structured format
            parsed_data = self._parse_llm_response(extracted_text, text)
            
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            # Fallback to basic extraction
            parsed_data = self._fallback_extraction(text)
        
        return parsed_data
    
    def _create_extraction_prompt(self, text, file_type):
        """Create a detailed extraction prompt"""
        
        # Get available categories for the prompt
        available_categories = category_manager.get_all_categories()
        categories_str = ", ".join(available_categories[:10])  # Limit for token count
        
        prompt = f"""Extract structured information from this {file_type} document and return it as valid JSON.

EXTRACTION REQUIREMENTS:
1. PROVIDER NAME: Extract the organization/provider name (company, nonprofit, agency, etc.)
2. CATEGORIES: Identify aid/service categories from this list: {categories_str}
3. CONTACTS: Find all emails, phone numbers, websites, and addresses  
4. DESCRIPTION: Write a concise summary of the main services or assistance offered

DOCUMENT CONTENT:
{text[:1500]}

Return your response as a valid JSON object with this exact structure:
{{
    "provider_name": "Name of the organization or provider",
    "categories": ["category1", "category2"],
    "contacts": {{
        "emails": ["email1@example.com"],
        "phones": ["123-456-7890"],
        "websites": ["https://example.com"],
        "addresses": ["Full address"]
    }},
    "description": "Brief description of services"
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _parse_llm_response(self, response_text, original_text):
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Normalize the extracted data
                provider_name = data.get('provider_name', 'Unknown Provider')
                
                # Normalize categories using category manager
                raw_categories = data.get('categories', [])
                categories = normalize_categories(raw_categories)
                
                # Extract contacts
                contacts = data.get('contacts', {})
                emails = contacts.get('emails', [])
                phones = contacts.get('phones', [])
                websites = contacts.get('websites', [])
                addresses = contacts.get('addresses', [])
                
                # Get description
                description = data.get('description', '')
                
                # If no description, generate one
                if not description and categories:
                    description = f"Provider offering {', '.join(categories)} services"
                
                return {
                    'provider_name': provider_name,
                    'categories': categories,
                    'emails': emails,
                    'phones': phones,
                    'websites': websites,
                    'addresses': addresses,
                    'description': description,
                    'raw_categories': raw_categories
                }
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            print(f"Response was: {response_text[:200]}...")
            return self._fallback_extraction(original_text)
    
    def _fallback_extraction(self, text):
        """Fallback extraction method using regex patterns"""
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Phone pattern (various formats)
        phone_pattern = r'\b(\(\d{3}\)\s*|\d{3}[-.])\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        
        # URL pattern
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        websites = re.findall(url_pattern, text)
        
        # Try to find provider name (look for patterns like "Company Name, Inc." etc.)
        provider_patterns = [
            r'([A-Z][A-Za-z\s&]+(?:Inc\.|LLC|Corporation|Corp\.|Company|Co\.|Foundation|Organization|Org\.|Agency|Services|Center|Centre))',
            r'^([A-Z][A-Za-z\s&]+)(?=\n|\r)',  # First line that starts with capital
        ]
        
        provider_name = "Unknown Provider"
        for pattern in provider_patterns:
            matches = re.findall(pattern, text[:500], re.MULTILINE)
            if matches:
                provider_name = matches[0].strip()
                break
        
        # Basic category detection
        categories = []
        text_lower = text.lower()
        
        # Check for category keywords
        category_keywords = {
            "Food Assistance": ["food", "meal", "nutrition", "pantry", "kitchen"],
            "Housing": ["housing", "shelter", "rent", "homeless"],
            "Medical": ["health", "medical", "clinic", "doctor", "hospital"],
            "Financial": ["financial", "money", "cash", "assistance", "benefit"],
            "Education": ["education", "school", "training", "tutor", "learning"],
            "Legal": ["legal", "law", "attorney", "court", "justice"],
            "Employment": ["job", "employment", "career", "work", "hiring"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        # Normalize categories
        categories = normalize_categories(categories) if categories else ["General Assistance"]
        
        # Generate description
        first_paragraph = text.split('\n\n')[0][:200]
        description = first_paragraph if first_paragraph else f"Provider offering {', '.join(categories)} services"
        
        return {
            'provider_name': provider_name,
            'categories': categories,
            'emails': list(set(emails))[:3],  # Limit to 3 unique emails
            'phones': list(set(phones))[:3],  # Limit to 3 unique phones
            'websites': list(set(websites))[:2],  # Limit to 2 unique websites
            'addresses': [],  # Address extraction is complex, leaving empty for fallback
            'description': description,
            'raw_categories': categories
        }
    
    def format_for_embedding(self, extracted_data):
        """Format extracted data for embedding storage - MUST match extraction.py format"""
        # Same implementation as original
        sections = []
        
        # Provider section
        if extracted_data.get('provider_name'):
            sections.append(f"PROVIDER: {extracted_data['provider_name']}")
        
        # Categories section
        if extracted_data.get('categories'):
            sections.append(f"CATEGORIES: {', '.join(extracted_data['categories'])}")
        
        # Contact information section
        contact_parts = []
        if extracted_data.get('emails'):
            contact_parts.append(f"Email: {', '.join(extracted_data['emails'])}")
        if extracted_data.get('phones'):
            contact_parts.append(f"Phone: {', '.join(extracted_data['phones'])}")
        if extracted_data.get('websites'):
            contact_parts.append(f"Website: {', '.join(extracted_data['websites'])}")
        if extracted_data.get('addresses'):
            contact_parts.append(f"Address: {'; '.join(extracted_data['addresses'])}")
        
        if contact_parts:
            sections.append("CONTACT INFORMATION:\n" + "\n".join(contact_parts))
        
        # Description section
        if extracted_data.get('description'):
            sections.append(f"DESCRIPTION: {extracted_data['description']}")
        
        return "\n\n".join(sections)

# Standalone function for compatibility with existing code
def extract_structured_data_llm(text, file_type="text"):
    """
    Standalone function that creates an LLMDataExtractor instance and extracts data.
    This function maintains compatibility with existing import statements.
    """
    extractor = LLMDataExtractor()
    return extractor.extract_structured_data(text, file_type)