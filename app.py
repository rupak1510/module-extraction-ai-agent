"""
Streamlit UI for Module Extractor.

Minimal UI for:
- Input: Documentation URLs
- Process: Extract modules
- Output: JSON display and download
"""

import streamlit as st
import json
import sys
import os
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.crawler_agent import CrawlerAgent
from agents.cleaner_agent import CleanerAgent
from agents.chunking_agent import ChunkingAgent
from agents.module_agent import ModuleAgent
from agents.dedup_agent import DedupAgent
from api.llm_client import GroqLLMClient


def extract_modules(urls: List[str]) -> List[dict]:
    """
    Main pipeline: Extract modules from documentation URLs.
    
    Args:
        urls: List of documentation URLs
        
    Returns:
        List of module dictionaries
    """
    # Initialize agents
    crawler = CrawlerAgent(max_pages=50, delay=0.5)
    cleaner = CleanerAgent()
    # Reduced chunk size for conceptual documentation (WordPress fix)
    chunker = ChunkingAgent(min_tokens=200, max_tokens=600)
    
    try:
        llm_client = GroqLLMClient(model="llama-3.1-70b-versatile")
    except Exception as e:
        st.error(f"Failed to initialize LLM client: {str(e)}")
        st.error("Please ensure GROQ_API_KEY environment variable is set.")
        return []
    
    module_agent = ModuleAgent(llm_client)
    dedup_agent = DedupAgent(llm_client, similarity_threshold=0.7)
    
    # Step 1: Crawl pages
    with st.spinner("Crawling documentation pages..."):
        pages = crawler.crawl(urls)
        st.info(f"Crawled {len(pages)} pages")
    
    if not pages:
        st.warning("No pages were successfully crawled.")
        return []
    
    # Step 2: Clean content
    with st.spinner("Cleaning HTML content..."):
        cleaned_pages = cleaner.clean(pages)
        st.info(f"Cleaned {len(cleaned_pages)} pages")
    
    if not cleaned_pages:
        st.warning("No content extracted after cleaning.")
        return []
    
    # Step 3: Chunk content
    with st.spinner("Chunking content..."):
        chunks = chunker.chunk(cleaned_pages)
        st.info(f"Created {len(chunks)} chunks")
    
    if not chunks:
        st.warning("No chunks created.")
        return []
    
    # Step 4: Infer modules
    with st.spinner("Inferring modules and submodules (this may take a while)..."):
        modules = module_agent.infer_modules(chunks)
        st.info(f"Found {len(modules)} modules")
    
    if not modules:
        st.warning("No modules inferred.")
        # Show debug info
        with st.expander("Debug Information"):
            st.write(f"Number of chunks processed: {len(chunks)}")
            if chunks:
                st.write("First chunk preview:")
                st.code(chunks[0].get('content', '')[:500])
                st.write(f"First chunk title: {chunks[0].get('title', 'N/A')}")
        return []
    
    # Step 5: Deduplicate
    with st.spinner("Deduplicating similar modules..."):
        final_modules = dedup_agent.deduplicate(modules)
        st.info(f"Final count: {len(final_modules)} modules after deduplication")
    
    return final_modules


def main():
    """Main Streamlit application."""
    st.title("Module Extractor")
    st.markdown("Extract modules and submodules from documentation websites using AI.")
    
    # API Key check
    import os
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ GROQ_API_KEY environment variable not set!")
        st.info("Please set your Groq API key as an environment variable before running the app.")
        st.code("export GROQ_API_KEY='your-api-key-here'", language="bash")
        return
    
    # URL input
    st.header("Input")
    url_input = st.text_area(
        "Enter documentation URLs (one per line):",
        height=100,
        placeholder="https://docs.example.com\nhttps://docs.example.com/getting-started"
    )
    
    # Extract button
    if st.button("Extract Modules", type="primary"):
        if not url_input.strip():
            st.warning("Please enter at least one URL.")
            return
        
        # Parse URLs
        urls = [url.strip() for url in url_input.split('\n') if url.strip()]
        
        if not urls:
            st.warning("No valid URLs found.")
            return
        
        # Extract modules
        modules = extract_modules(urls)
        
        if modules:
            # Display results
            st.header("Output")
            
            # Format JSON
            json_output = json.dumps(modules, indent=2, ensure_ascii=False)
            
            # Display JSON
            st.json(modules)
            
            # Download button
            st.download_button(
                label="Download JSON",
                data=json_output,
                file_name="modules.json",
                mime="application/json"
            )
        else:
            st.warning("No modules were extracted. Please check the URLs and try again.")


if __name__ == "__main__":
    main()

