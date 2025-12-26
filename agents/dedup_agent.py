"""
Deduplication Agent: Merges semantically similar modules.

Responsibility: Identify and merge modules that are semantically similar,
using similarity comparison and LLM-based reasoning when needed.
"""

from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.similarity_utils import are_similar, merge_modules
from api.llm_client import GroqLLMClient


class DedupAgent:
    """
    Agent responsible for deduplicating semantically similar modules.
    
    Uses:
    - Similarity comparison for initial filtering
    - LLM-based reasoning for complex cases
    """
    
    def __init__(self, llm_client: GroqLLMClient, similarity_threshold: float = 0.7):
        """
        Initialize the deduplication agent.
        
        Args:
            llm_client: Initialized GroqLLMClient instance
            similarity_threshold: Threshold for considering modules similar (0-1)
        """
        self.llm_client = llm_client
        self.similarity_threshold = similarity_threshold
    
    def deduplicate(self, modules: List[Dict]) -> List[Dict]:
        """
        Deduplicate modules by merging similar ones.
        
        Args:
            modules: List of module dictionaries
            
        Returns:
            Deduplicated list of modules
        """
        if not modules:
            return []
        
        # First pass: Use similarity-based deduplication
        deduplicated = self._similarity_deduplicate(modules)
        
        # Second pass: Use LLM for complex cases
        deduplicated = self._llm_deduplicate(deduplicated)
        
        return deduplicated
    
    def _similarity_deduplicate(self, modules: List[Dict]) -> List[Dict]:
        """
        Deduplicate using similarity comparison.
        
        Args:
            modules: List of modules
            
        Returns:
            Deduplicated list
        """
        if len(modules) <= 1:
            return modules
        
        merged = []
        used_indices = set()
        
        for i, module1 in enumerate(modules):
            if i in used_indices:
                continue
            
            current_module = module1.copy()
            
            # Check against remaining modules
            for j, module2 in enumerate(modules[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                if are_similar(current_module, module2, self.similarity_threshold):
                    current_module = merge_modules(current_module, module2)
                    used_indices.add(j)
            
            merged.append(current_module)
            used_indices.add(i)
        
        return merged
    
    def _llm_deduplicate(self, modules: List[Dict]) -> List[Dict]:
        """
        Use LLM to identify and merge similar modules.
        
        Args:
            modules: List of modules
            
        Returns:
            Further deduplicated list
        """
        if len(modules) <= 1:
            return modules
        
        # For large lists, process in batches
        if len(modules) > 10:
            # Process in smaller batches
            batch_size = 10
            result = []
            for i in range(0, len(modules), batch_size):
                batch = modules[i:i + batch_size]
                deduped_batch = self._llm_deduplicate_batch(batch)
                result.extend(deduped_batch)
            return result
        else:
            return self._llm_deduplicate_batch(modules)
    
    def _llm_deduplicate_batch(self, modules: List[Dict]) -> List[Dict]:
        """
        Use LLM to deduplicate a batch of modules.
        
        Args:
            modules: List of modules (max 10)
            
        Returns:
            Deduplicated modules
        """
        if len(modules) <= 1:
            return modules
        
        # Create context for LLM
        modules_json = "\n".join([
            f"{i+1}. Module: {m.get('module', '')} - {m.get('Description', '')[:100]}"
            for i, m in enumerate(modules)
        ])
        
        prompt = f"""Review the following list of modules and identify which ones are duplicates or should be merged.

Modules:
{modules_json}

Return a JSON object with:
- "duplicates": List of lists, where each inner list contains indices (1-based) of modules that should be merged
- "keep": List of indices (1-based) of modules to keep as-is

Example:
{{
  "duplicates": [[1, 3], [2, 5]],
  "keep": [4, 6]
}}

If no duplicates found, return {{"duplicates": [], "keep": [1, 2, 3, ...]}}"""
        
        try:
            response = self.llm_client.generate_json(prompt, temperature=0.1)
            
            # Process duplicates
            duplicates = response.get("duplicates", [])
            keep_indices = set(response.get("keep", []))
            
            # Merge duplicates
            merged_modules = []
            processed_indices = set()
            
            # Process duplicate groups
            for dup_group in duplicates:
                if not dup_group:
                    continue
                
                # Convert to 0-based indices
                indices = [idx - 1 for idx in dup_group if 0 < idx <= len(modules)]
                
                if len(indices) > 1:
                    # Merge modules in this group
                    merged = modules[indices[0]].copy()
                    for idx in indices[1:]:
                        merged = merge_modules(merged, modules[idx])
                    merged_modules.append(merged)
                    processed_indices.update(indices)
            
            # Add modules to keep
            for idx in keep_indices:
                zero_based_idx = idx - 1
                if 0 <= zero_based_idx < len(modules) and zero_based_idx not in processed_indices:
                    merged_modules.append(modules[zero_based_idx])
            
            # If LLM response is invalid, return original modules
            if not merged_modules:
                return modules
            
            return merged_modules
            
        except Exception as e:
            print(f"LLM deduplication failed: {str(e)}. Using similarity-based result.")
            return modules

