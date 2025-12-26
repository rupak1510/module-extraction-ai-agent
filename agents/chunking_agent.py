"""
Chunking Agent: Splits content into manageable chunks.

Responsibility: Break down cleaned content into 500-800 token chunks
while preserving semantic structure (keeping headings with their content).
"""

from typing import List, Dict
import tiktoken


class ChunkingAgent:
    """
    Agent responsible for chunking content into token-sized blocks.
    
    Features:
    - Chunks content into 500-800 token blocks
    - Preserves semantic structure
    - Keeps headings with their related content
    """
    
    def __init__(self, min_tokens: int = 500, max_tokens: int = 800):
        """
        Initialize the chunking agent.
        
        Args:
            min_tokens: Minimum tokens per chunk
            max_tokens: Maximum tokens per chunk
        """
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        # Use cl100k_base encoding (GPT-4 tokenizer, works well for general text)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except:
            # Fallback: simple token estimation (4 chars per token)
            self.encoder = None
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: approximate (4 characters per token)
            return len(text) // 4
    
    def chunk(self, pages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Chunk pages into token-sized blocks.
        
        Args:
            pages: List of page dictionaries with 'url', 'content', and 'title'
            
        Returns:
            List of chunk dictionaries with 'url', 'content', 'title', and 'chunk_index'
        """
        chunks = []
        
        for page in pages:
            content = page.get("content", "")
            url = page.get("url", "")
            title = page.get("title", "")
            
            if not content.strip():
                continue
            
            # Split content by headings to preserve semantic structure
            lines = content.split('\n')
            current_chunk = []
            current_tokens = 0
            
            for line in lines:
                line_tokens = self._count_tokens(line)
                
                # If adding this line would exceed max_tokens, save current chunk
                if (current_tokens + line_tokens > self.max_tokens and 
                    current_tokens >= self.min_tokens):
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append({
                            "url": url,
                            "content": chunk_text,
                            "title": title,
                            "chunk_index": len([c for c in chunks if c["url"] == url])
                        })
                    current_chunk = [line]
                    current_tokens = line_tokens
                else:
                    current_chunk.append(line)
                    current_tokens += line_tokens
            
            # Add remaining chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        "url": url,
                        "content": chunk_text,
                        "title": title,
                        "chunk_index": len([c for c in chunks if c["url"] == url])
                    })
        
        return chunks

