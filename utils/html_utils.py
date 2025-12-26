"""
HTML utility functions for parsing and cleaning HTML content.
"""

from typing import List, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag, NavigableString
import re


def extract_internal_links(html: str, base_url: str) -> Set[str]:
    """
    Extract all internal links from HTML content.
    
    Args:
        html: HTML content as string
        base_url: Base URL to determine internal links
        
    Returns:
        Set of internal URLs (absolute)
    """
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(base_url).netloc
    base_scheme = urlparse(base_url).scheme
    
    internal_links = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)
        
        # Check if it's an internal link (same domain)
        if parsed.netloc == base_domain or (not parsed.netloc and parsed.path):
            # Remove fragments
            clean_url = f"{parsed.scheme or base_scheme}://{parsed.netloc or base_domain}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"
            
            # Only include http/https URLs
            if clean_url.startswith(('http://', 'https://')):
                internal_links.add(clean_url)
    
    return internal_links


def clean_html_content(html: str) -> str:
    """
    Extract meaningful content from HTML, removing navigation, headers, footers.
    
    Keeps only:
    - Headings (h1-h6)
    - Paragraphs
    - Lists (ul, ol)
    - Code blocks (pre, code)
    
    Args:
        html: Raw HTML content
        
    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, nav, header, footer, aside elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Remove common navigation classes/ids
    for element in soup.find_all(class_=re.compile(r'nav|menu|sidebar|header|footer', re.I)):
        element.decompose()
    
    for element in soup.find_all(id=re.compile(r'nav|menu|sidebar|header|footer', re.I)):
        element.decompose()
    
    # Extract meaningful content
    content_parts = []
    
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'pre', 'code', 'blockquote']):
        text = element.get_text(separator=' ', strip=True)
        if text and len(text) > 10:  # Filter out very short text
            # Add heading markers
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                content_parts.append(f"\n{'#' * level} {text}\n")
            elif element.name == 'li':
                content_parts.append(f"- {text}")
            else:
                content_parts.append(text)
    
    return '\n'.join(content_parts)


def get_page_title(html: str) -> str:
    """
    Extract page title from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        Page title or empty string
    """
    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""

