"""
Content Cleaner Agent: Cleans and extracts meaningful content from HTML.

Responsibility: Remove navigation elements, headers, footers, and extract
only meaningful documentation content (headings, paragraphs, lists).
"""

from typing import List, Dict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.html_utils import clean_html_content, get_page_title


class CleanerAgent:
    """
    Agent responsible for cleaning HTML content.
    
    Removes:
    - Navigation bars
    - Headers and footers
    - Sidebars
    - Scripts and styles
    
    Keeps:
    - Headings (h1-h6)
    - Paragraphs
    - Lists
    - Code blocks
    """
    
    def __init__(self):
        """Initialize the cleaner agent."""
        pass
    
    def clean(self, pages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Clean HTML content from multiple pages.
        
        Args:
            pages: List of page dictionaries with 'url' and 'html' keys
            
        Returns:
            List of cleaned page dictionaries with 'url', 'content', and 'title'
        """
        cleaned_pages = []
        
        for page in pages:
            if page.get("status") != "success" or not page.get("html"):
                continue
            
            html = page["html"]
            url = page["url"]
            
            # Clean HTML content
            cleaned_content = clean_html_content(html)
            
            # Extract title
            title = get_page_title(html)
            
            if cleaned_content.strip():  # Only add if there's content
                cleaned_pages.append({
                    "url": url,
                    "content": cleaned_content,
                    "title": title
                })
        
        return cleaned_pages

