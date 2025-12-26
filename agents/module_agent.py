"""
Module Inference Agent: Infers modules and submodules from content.

Responsibility: Use LLM to analyze content chunks and extract:
- Top-level modules
- Submodules
- Descriptions
- Logical hierarchy

Must avoid hallucination and use ONLY provided content.
"""

from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.llm_client import GroqLLMClient


class ModuleAgent:
    """
    Agent responsible for inferring modules and submodules from content.
    
    Uses LLM to:
    - Identify modules and submodules
    - Generate descriptions
    - Maintain logical hierarchy
    - Avoid hallucination
    """
    
    def __init__(self, llm_client: GroqLLMClient):
        """
        Initialize the module inference agent.
        
        Args:
            llm_client: Initialized GroqLLMClient instance
        """
        self.llm_client = llm_client
    
    def infer_modules(self, chunks: List[Dict[str, str]]) -> List[Dict]:
        """
        Infer modules and submodules from content chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'content', 'url', 'title'
            
        Returns:
            List of module dictionaries with 'module', 'Description', 'Submodules'
        """
        all_modules = []
        
        # Process chunks one at a time to avoid Groq 400 errors
        batch_size = 1
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Skip empty batches
            if not batch:
                continue
            
            # Combine batch content
            batch_content = "\n\n---\n\n".join([
                f"Page: {chunk.get('title', chunk.get('url', ''))}\n{chunk.get('content', '')}"
                for chunk in batch if chunk.get('content', '').strip()
            ])
            
            # Skip if no content
            if not batch_content.strip():
                continue
            
            # Truncate content if too long (Groq has token limits)
            max_content_length = 8000  # Approximate character limit
            if len(batch_content) > max_content_length:
                batch_content = batch_content[:max_content_length] + "\n\n[Content truncated...]"
            
            # Create prompt with content embedded directly (no separate context parameter)
            prompt = self._create_inference_prompt(batch_content)
            
            try:
                # Get LLM response - content is already in prompt, do NOT pass as context
                response = self.llm_client.generate_json(
                    prompt=prompt,
                    context="",  # Empty - content is embedded in prompt
                    temperature=0.1  # Low temperature for deterministic output
                )
                
                # Extract modules from response
                modules = self._extract_modules_from_response(response)
                # Filter out empty modules
                modules = [m for m in modules if m.get('module', '').strip()]
                all_modules.extend(modules)
                
            except Exception as e:
                # Safe error logging
                try:
                    error_msg = str(e)
                    batch_num = (i // batch_size) + 1 if batch_size > 0 else 1
                    print(f"Error inferring modules from batch {batch_num}: {error_msg}")
                except:
                    print(f"Error inferring modules from batch (error details unavailable)")
                continue
        
        # Safety fallback: if no modules found, run relaxed inference on first chunk
        if not all_modules and chunks:
            try:
                # Try all chunks in fallback, not just first
                for chunk in chunks[:3]:  # Try first 3 chunks
                    chunk_content = chunk.get('content', '')
                    if not chunk_content or len(chunk_content.strip()) < 50:
                        continue
                    
                    fallback_prompt = """You are analyzing product documentation.

CRITICAL: You MUST extract modules from this content. Look for:
- Product names or product areas (e.g., Billing, Payments, Receivables)
- Feature names or categories
- Section headings or major topics
- Documentation categories

Even if the content is minimal, identify the main topics as modules.

Return JSON in this format (MUST have at least one module):
{
  "modules": [
    {
      "module": "Module Name",
      "Description": "Description based on content",
      "Submodules": {}
    }
  ]
}

CONTENT:
""" + chunk_content
                    
                    response = self.llm_client.generate_json(
                        prompt=fallback_prompt,
                        context="",  # Content embedded in prompt
                        temperature=0.3  # Slightly higher for more creative extraction
                    )
                    fallback_modules = self._extract_modules_from_response(response)
                    if fallback_modules:
                        all_modules.extend(fallback_modules)
                        break  # Stop if we found modules
            except Exception as e:
                # Safe error logging
                try:
                    print(f"Fallback inference failed: {str(e)}")
                except:
                    print("Fallback inference failed (error details unavailable)")
        
        # Final safety: if still no modules, create a generic one from page title/URL
        if not all_modules and chunks:
            # Extract any meaningful text from first chunk
            first_chunk = chunks[0]
            title = first_chunk.get('title', '')
            url = first_chunk.get('url', '')
            content_preview = first_chunk.get('content', '')[:200]
            
            # Try to extract module name from title or URL
            module_name = title or url.split('/')[-1] or "Documentation"
            if module_name and module_name != "Documentation":
                all_modules.append({
                    "module": module_name,
                    "Description": f"Documentation section: {content_preview[:100]}...",
                    "Submodules": {}
                })

        return all_modules
    
    def _create_inference_prompt(self, content: str) -> str:
        """
        Create prompt for module inference with content embedded.
        
        Args:
            content: Content to analyze (will be embedded in prompt)
            
        Returns:
            Formatted prompt string with content embedded
        """
        return """You are analyzing product documentation.

IMPORTANT DEFINITIONS:
- A "Module" is a MAJOR PRODUCT AREA, FEATURE, or DOCUMENTATION CATEGORY.
- Modules may represent guides, concepts, setup steps, major sections, or product suites.
- Examples of valid modules include:
  - Billing, Payments, Receivables (product areas)
  - Getting Started, Installation (guides)
  - Themes, Plugins (features)
  - Customization, Security (categories)
  - Content Management (concepts)

A "Submodule" is a specific task, feature, or concept within a module.

CRITICAL RULES:
1. You MUST identify high-level documentation categories as modules
2. If you see product names, feature names, or section headings, treat them as modules
3. DO NOT return an empty list - ALWAYS find at least one module from the content
4. Use ONLY the provided content
5. Group related topics logically
6. Avoid hallucination or invented features
7. Generate concise, factual descriptions
8. If content mentions "Billing", "Payments", "Receivables", etc., these are modules
9. If content lists product areas or features, extract them as modules

Return STRICT JSON only, using this format:

{
  "modules": [
    {
      "module": "Module Name",
      "Description": "Description based strictly on content",
      "Submodules": {
        "Submodule Name": "Description"
      }
    }
  ]
}

YOU MUST RETURN AT LEAST ONE MODULE. If the content mentions any product areas, features, or sections, extract them.

CONTENT:
""" + content
    
    def _extract_modules_from_response(self, response: Dict) -> List[Dict]:
        """
        Extract modules from LLM response.
        
        Args:
            response: LLM JSON response
            
        Returns:
            List of module dictionaries
        """
        modules = []
        
        if isinstance(response, dict):
            if "modules" in response:
                modules = response["modules"]
                # Handle empty modules array - try to extract from other fields
                if not modules and isinstance(response["modules"], list) and len(response["modules"]) == 0:
                    # Check if there are other keys that might contain module info
                    for key, value in response.items():
                        if key != "modules" and isinstance(value, (list, dict)):
                            if isinstance(value, list) and value:
                                modules = value
                                break
                            elif isinstance(value, dict) and "module" in value:
                                modules = [value]
                                break
            elif "module" in response:
                # Single module format
                modules = [response]
            else:
                # Try to find modules in any key
                for key, value in response.items():
                    if isinstance(value, list) and value:
                        modules = value
                        break
                    elif isinstance(value, dict) and "module" in value:
                        modules = [value]
                        break
        
        # Ensure proper format
        formatted_modules = []
        for module in modules:
            if isinstance(module, dict):
                module_name = module.get("module", "").strip()
                # Only add if module has a name
                if module_name:
                    formatted_modules.append({
                        "module": module_name,
                        "Description": module.get("Description", "").strip() or f"Documentation for {module_name}",
                        "Submodules": module.get("Submodules", {}) or {}
                    })
        
        return formatted_modules

