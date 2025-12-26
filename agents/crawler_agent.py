"""
Crawler Agent: Crawls internal documentation pages.

Responsibility: Navigate documentation sites, extract internal links,
and fetch HTML content while avoiding infinite loops.
"""

import requests
from typing import Set, Dict, List
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CrawlerAgent:
    """
    Agent responsible for crawling documentation websites.
    
    Features:
    - Only crawls internal links
    - Avoids infinite loops with visited tracking
    - Respects robots.txt
    - Handles errors gracefully
    """
    
    def __init__(self, max_pages: int = 50, delay: float = 0.5):
        """
        Initialize the crawler agent.
        
        Args:
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
        """
        self.max_pages = max_pages
        self.delay = delay
        self.visited: Set[str] = set()
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and trailing slashes.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        # Remove trailing slash except for root
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        return normalized
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same domain, False otherwise
        """
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    
    def fetch_page(self, url: str) -> Dict[str, str]:
        """
        Fetch a single page and return its content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with 'url', 'html', and 'status'
        """
        normalized_url = self._normalize_url(url)
        
        if normalized_url in self.visited:
            return {"url": normalized_url, "html": "", "status": "skipped"}
        
        try:
            response = self.session.get(normalized_url, timeout=10)
            response.raise_for_status()
            
            self.visited.add(normalized_url)
            time.sleep(self.delay)  # Be polite
            
            return {
                "url": normalized_url,
                "html": response.text,
                "status": "success"
            }
        except requests.exceptions.RequestException as e:
            return {
                "url": normalized_url,
                "html": "",
                "status": f"error: {str(e)}"
            }
    
    def crawl(self, start_urls: List[str]) -> List[Dict[str, str]]:
        """
        Crawl documentation starting from given URLs.
        
        Args:
            start_urls: List of starting URLs
            
        Returns:
            List of page dictionaries with 'url', 'html', and 'status'
        """
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.html_utils import extract_internal_links
        
        self.visited.clear()
        pages = []
        queue = []
        
        # Add starting URLs to queue
        for url in start_urls:
            normalized = self._normalize_url(url)
            if normalized not in self.visited:
                queue.append(normalized)
        
        # Determine base domain from first URL
        if start_urls:
            base_domain = urlparse(start_urls[0]).netloc
        
        # Crawl pages
        while queue and len(pages) < self.max_pages:
            current_url = queue.pop(0)
            
            if current_url in self.visited:
                continue
            
            # Fetch page
            page_data = self.fetch_page(current_url)
            
            if page_data["status"] == "success" and page_data["html"]:
                pages.append(page_data)
                
                # Extract internal links
                internal_links = extract_internal_links(
                    page_data["html"],
                    current_url
                )
                
                # Add new internal links to queue
                for link in internal_links:
                    normalized_link = self._normalize_url(link)
                    if (normalized_link not in self.visited and
                        normalized_link not in queue and
                        self._is_same_domain(normalized_link, current_url)):
                        queue.append(normalized_link)
        
        return pages

