"""
Similarity utility functions for semantic comparison and deduplication.
"""

from typing import List, Dict, Tuple
import re


def simple_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score between two texts.
    
    Uses word overlap and normalized edit distance.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize texts
    def normalize(text: str) -> List[str]:
        words = re.findall(r'\b\w+\b', text.lower())
        return sorted(set(words))
    
    words1 = normalize(text1)
    words2 = normalize(text2)
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(set(words1) & set(words2))
    union = len(set(words1) | set(words2))
    
    if union == 0:
        return 0.0
    
    jaccard = intersection / union
    
    # Calculate word overlap
    overlap = intersection / min(len(words1), len(words2))
    
    # Combined score
    return (jaccard * 0.6 + overlap * 0.4)


def are_similar(module1: Dict, module2: Dict, threshold: float = 0.7) -> bool:
    """
    Check if two modules are semantically similar.
    
    Args:
        module1: First module dictionary
        module2: Second module dictionary
        threshold: Similarity threshold (default 0.7)
        
    Returns:
        True if modules are similar, False otherwise
    """
    # Compare module names
    name_sim = simple_similarity(
        module1.get("module", ""),
        module2.get("module", "")
    )
    
    # Compare descriptions
    desc_sim = simple_similarity(
        module1.get("Description", ""),
        module2.get("Description", "")
    )
    
    # Combined similarity
    combined_sim = (name_sim * 0.6 + desc_sim * 0.4)
    
    return combined_sim >= threshold


def merge_modules(module1: Dict, module2: Dict) -> Dict:
    """
    Merge two similar modules into one.
    
    Args:
        module1: First module dictionary
        module2: Second module dictionary
        
    Returns:
        Merged module dictionary
    """
    # Use the longer/more descriptive name
    name1 = module1.get("module", "")
    name2 = module2.get("module", "")
    merged_name = name1 if len(name1) >= len(name2) else name2
    
    # Combine descriptions
    desc1 = module1.get("Description", "")
    desc2 = module2.get("Description", "")
    merged_desc = f"{desc1} {desc2}".strip()
    if len(desc1) > len(desc2):
        merged_desc = desc1
    
    # Merge submodules
    submodules1 = module1.get("Submodules", {})
    submodules2 = module2.get("Submodules", {})
    merged_submodules = {**submodules1, **submodules2}
    
    return {
        "module": merged_name,
        "Description": merged_desc,
        "Submodules": merged_submodules
    }

