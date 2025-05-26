"""
Category management and normalization for RAG system
"""
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import os

# Define aid categories with synonyms
DEFAULT_CATEGORIES = {
    "food": ["food", "meal", "nutrition", "hunger", "feeding", "grocery", "pantry", "snap", "ebt", "food bank", "meals", "food stamps"],
    "housing": ["housing", "shelter", "lodging", "home", "apartment", "rent", "homeless", "accommodation", "eviction", "housing assistance"],
    "healthcare": ["healthcare", "medical", "health", "clinic", "hospital", "doctor", "medicine", "dental", "mental health", "prescription"],
    "financial": ["financial", "money", "cash", "assistance", "aid", "stipend", "subsidy", "income", "welfare", "tanf", "financial aid"],
    "employment": ["employment", "job", "career", "work", "hiring", "resume", "interview", "unemployment", "workforce", "job training"],
    "education": ["education", "school", "training", "class", "course", "learning", "tuition", "scholarship", "academic", "college"],
    "childcare": ["childcare", "daycare", "child care", "babysitting", "children", "kids", "youth", "family", "after school", "child support"],
    "transportation": ["transportation", "transit", "bus", "ride", "car", "vehicle", "train", "travel", "transport", "transportation assistance"],
    "legal": ["legal", "law", "attorney", "lawyer", "rights", "advocacy", "court", "justice", "representation", "legal aid"],
    "utilities": ["utilities", "utility", "electric", "gas", "water", "bill", "power", "energy", "liheap", "utility assistance"],
    "seniors": ["seniors", "elderly", "aging", "older adults", "retirement", "medicare", "social security", "senior services"],
    "veterans": ["veterans", "military", "service member", "va", "veteran affairs", "veteran benefits", "veteran services"],
    "disaster": ["disaster", "emergency", "crisis", "relief", "fema", "natural disaster", "hurricane", "flood", "fire", "emergency relief"],
    "immigration": ["immigration", "immigrant", "refugee", "asylum", "citizenship", "documentation", "migrant", "immigration services"],
    "counseling": ["counseling", "therapy", "support group", "mental health", "crisis", "hotline", "suicide", "addiction", "recovery"]
}

class CategoryManager:
    """Manages aid categories and provides normalization capabilities"""
    
    def __init__(self, custom_categories_path=None):
        """
        Initialize the category manager
        
        Args:
            custom_categories_path: Optional path to JSON file with custom categories
        """
        self.categories = DEFAULT_CATEGORIES.copy()
        
        # Load custom categories if provided
        if custom_categories_path and os.path.exists(custom_categories_path):
            try:
                with open(custom_categories_path, 'r') as f:
                    custom_categories = json.load(f)
                    # Merge with default categories
                    for category, synonyms in custom_categories.items():
                        if category in self.categories:
                            # Add new synonyms to existing category
                            self.categories[category] = list(set(self.categories[category] + synonyms))
                        else:
                            # Add new category
                            self.categories[category] = synonyms
            except Exception as e:
                print(f"Error loading custom categories: {str(e)}")
        
        # Create vectorizer for semantic matching
        self._create_vectorizer()
    
    def _create_vectorizer(self):
        """Create TF-IDF vectorizer for semantic matching"""
        # Flatten all synonyms into a single list
        all_synonyms = [syn for synonyms in self.categories.values() for syn in synonyms]
        
        # Create and fit vectorizer
        self.vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2))
        self.vectorizer.fit(all_synonyms)
        
        # Create matrix of all synonyms
        self.synonym_matrix = self.vectorizer.transform(all_synonyms)
        
        # Map each synonym to its category
        self.synonym_to_category = {}
        for category, synonyms in self.categories.items():
            for synonym in synonyms:
                self.synonym_to_category[synonym] = category
    
    def normalize_category(self, text, threshold=0.7):
        """
        Find the most likely category for a given text
        
        Args:
            text: Text to categorize
            threshold: Similarity threshold (0-1)
            
        Returns:
            Tuple of (normalized_category, confidence_score)
        """
        # Try direct matching first
        text_lower = text.lower()
        
        # Check if text directly matches a category name
        if text_lower in self.categories:
            return text_lower, 1.0
            
        # Check if text directly matches a synonym
        for category, synonyms in self.categories.items():
            if text_lower in synonyms:
                return category, 1.0
        
        # Try fuzzy matching
        best_match = process.extractOne(text_lower, list(self.synonym_to_category.keys()))
        if best_match and best_match[1] >= threshold * 100:  # fuzzywuzzy returns percentage
            return self.synonym_to_category[best_match[0]], best_match[1] / 100
            
        # Try semantic matching with TF-IDF
        try:
            # Transform the input text
            text_vector = self.vectorizer.transform([text_lower])
            
            # Calculate similarities with all synonyms
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(text_vector, self.synonym_matrix).flatten()
            
            # Find the best match
            best_idx = similarities.argmax()
            best_score = similarities[best_idx]
            
            if best_score >= threshold:
                # Get the synonym and its category
                best_synonym = list(self.synonym_to_category.keys())[best_idx]
                return self.synonym_to_category[best_synonym], best_score
        except Exception as e:
            print(f"Error in semantic matching: {str(e)}")
        
        # No good match found
        return None, 0.0
    
    def get_all_categories(self):
        """Get all available categories"""
        return list(self.categories.keys())
    
    def get_synonyms(self, category):
        """Get all synonyms for a category"""
        return self.categories.get(category, [])
    
    def add_synonym(self, category, synonym):
        """Add a new synonym to a category"""
        if category in self.categories:
            if synonym not in self.categories[category]:
                self.categories[category].append(synonym)
                # Recreate vectorizer with new synonym
                self._create_vectorizer()
            return True
        return False
    
    def save_custom_categories(self, filepath):
        """Save current categories to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.categories, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving categories: {str(e)}")
            return False

# Create a default instance
category_manager = CategoryManager()

def normalize_categories(extracted_categories):
    """
    Normalize a dictionary of extracted categories
    
    Args:
        extracted_categories: Dictionary from extraction module
        
    Returns:
        Dictionary of normalized categories with confidence scores
    """
    normalized = {}
    
    # Process each extracted category
    for category_name, matches in extracted_categories.items():
        # Try to normalize the category name itself
        norm_category, confidence = category_manager.normalize_category(category_name)
        
        if norm_category:
            if norm_category not in normalized or confidence > normalized[norm_category]:
                normalized[norm_category] = confidence
    
    # Also process the matches themselves to find potential categories
    for matches_list in extracted_categories.values():
        for match in matches_list:
            norm_category, confidence = category_manager.normalize_category(match)
            if norm_category:
                if norm_category not in normalized or confidence > normalized[norm_category]:
                    normalized[norm_category] = confidence
    
    return normalized