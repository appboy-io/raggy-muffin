import spacy
import re
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from categories import category_manager, normalize_categories

# Load spaCy model - download with: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, download it
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Regular expressions for contact information
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'\b(\(\d{3}\)\s*|\d{3}[-.])\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
ADDRESS_PATTERN = r'\b\d+\s+[A-Za-z0-9\s,.-]+\b(?:avenue|ave|street|st|road|rd|boulevard|blvd|drive|dr|lane|ln|court|ct|way|parkway|pkwy|place|pl)\b'

def extract_structured_data(text):
    """
    Extract structured data from text including:
    - Provider name
    - Aid categories
    - Contact information
    - Service description
    """
    # Process with spaCy
    doc = nlp(text)
    
    # Extract provider name
    provider_name = extract_provider_name(text, doc)
    
    # Extract categories
    categories = extract_categories(text)
    
    # Extract contact information
    contacts = {
        "emails": re.findall(EMAIL_PATTERN, text, re.IGNORECASE),
        "phones": re.findall(PHONE_PATTERN, text),
        "urls": re.findall(URL_PATTERN, text),
        "addresses": extract_addresses(doc)
    }
    
    # Extract service description
    description = extract_service_description(text, doc)
    
    return {
        "provider_name": provider_name,
        "categories": categories,
        "contacts": contacts,
        "description": description
    }

def extract_provider_name(text, doc):
    """Extract provider/organization name using spaCy NER and patterns"""
    # First try spaCy's named entity recognition for organizations
    org_entities = [ent.text for ent in doc.ents if ent.label_ in ["ORG"]]
    
    # Filter out common false positives
    false_positives = ["email", "phone", "website", "address", "contact", "information"]
    org_entities = [org for org in org_entities if not any(fp in org.lower() for fp in false_positives)]
    
    if org_entities:
        # Return the longest organization name (likely most complete)
        return max(org_entities, key=len)
    
    # Fallback to pattern-based extraction
    lines = text.split('\n')
    
    # Look for common provider name patterns
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
            
        # Look for organization indicators
        org_patterns = [
            r'^([A-Z][A-Za-z\s&,.-]+(?:Inc\.?|LLC|Corp\.?|Foundation|Center|Agency|Services|Association|Organization|Department))',
            r'^([A-Z][A-Za-z\s&,.-]{5,50})\s*$',  # Title case lines (likely org names)
            r'Organization[:\s]+([A-Za-z\s&,.-]+)',
            r'Provider[:\s]+([A-Za-z\s&,.-]+)',
            r'Agency[:\s]+([A-Za-z\s&,.-]+)',
            r'Department[:\s]+([A-Za-z\s&,.-]+)'
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 100:  # Reasonable length
                    return name
    
    # If no pattern matches, try first meaningful line that looks like a title
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 10 and len(line) < 80:
            # Skip lines that look like categories or contact info
            skip_patterns = ['email', 'phone', 'address', 'website', 'http', '@', 'contact', 'categories']
            if not any(skip in line.lower() for skip in skip_patterns):
                # Check if it's mostly title case (likely an organization name)
                words = line.split()
                if len(words) >= 2 and sum(1 for w in words if w[0].isupper()) >= len(words) * 0.6:
                    return line
    
    return ""

def extract_categories(text):
    """Extract aid categories from text using fuzzy matching"""
    found_categories = {}
    
    # Convert text to lowercase for better matching
    text_lower = text.lower()
    
    # Use the category manager to find categories and synonyms
    categories = category_manager.get_all_categories()
    
    # Extract potential category words from text
    words = text_lower.split()
    potential_category_terms = []
    
    # Single words
    for word in words:
        if len(word) > 3:  # Only consider words with length > 3
            potential_category_terms.append(word)
    
    # Bigrams (pairs of words)
    for i in range(len(words) - 1):
        if len(words[i]) > 2 and len(words[i+1]) > 2:  # Avoid very short words
            bigram = words[i] + " " + words[i+1]
            potential_category_terms.append(bigram)
    
    # Try to match each potential term
    for term in potential_category_terms:
        # Get the category for this term
        norm_category, confidence = category_manager.normalize_category(term, threshold=0.65)
        
        if norm_category:
            if norm_category in found_categories:
                found_categories[norm_category].append(term)
            else:
                found_categories[norm_category] = [term]
    
    return found_categories

def extract_addresses(doc):
    """Extract addresses using spaCy's NER"""
    addresses = []
    
    # Look for GPE (Geo-Political Entity) and LOC (Location) entities
    address_entities = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
    
    # Use regex to find address patterns
    address_matches = re.findall(ADDRESS_PATTERN, doc.text, re.IGNORECASE)
    
    # Combine both approaches
    addresses = list(set(address_entities + address_matches))
    
    return addresses

def extract_service_description(text, doc):
    """Extract service description using key sentences"""
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # Look for sentences that mention services or assistance
    service_keywords = ["provide", "offer", "service", "assist", "help", "support", "available", "resource"]
    
    service_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in service_keywords):
            service_sentences.append(sentence)
    
    # If we found specific service sentences, use those
    if service_sentences:
        return " ".join(service_sentences)
    
    # Otherwise, just return first few sentences as a summary
    return " ".join(sentences[:3]) if sentences else ""

def normalize_text(extracted_data):
    """
    Convert extracted structured data back to normalized text format
    suitable for embedding and retrieval
    """
    normalized_text = ""
    
    # Add provider name
    if extracted_data.get("provider_name"):
        normalized_text += "PROVIDER: " + extracted_data["provider_name"] + "\n\n"
    
    # Add categories with normalization
    if extracted_data["categories"]:
        # Normalize categories to standard format
        normalized_categories = normalize_categories(extracted_data["categories"])
        
        # Add to normalized text with confidence scores (if high enough)
        if normalized_categories:
            categories_list = []
            for category, confidence in normalized_categories.items():
                if confidence >= 0.75:  # Only include high confidence categories
                    categories_list.append(category)
            
            if categories_list:
                normalized_text += "CATEGORIES: " + ", ".join(categories_list) + "\n\n"
    
    # Add contact information
    contacts = extracted_data["contacts"]
    contact_section = "CONTACT INFORMATION:\n"
    
    if contacts["emails"]:
        contact_section += "Email: " + ", ".join(contacts["emails"]) + "\n"
    
    if contacts["phones"]:
        contact_section += "Phone: " + ", ".join(contacts["phones"]) + "\n"
    
    if contacts["urls"]:
        contact_section += "Website: " + ", ".join(contacts["urls"]) + "\n"
    
    if contacts["addresses"]:
        contact_section += "Address: " + ", ".join(contacts["addresses"]) + "\n"
    
    normalized_text += contact_section + "\n"
    
    # Add description
    if extracted_data["description"]:
        normalized_text += "DESCRIPTION:\n" + extracted_data["description"] + "\n"
    
    return normalized_text