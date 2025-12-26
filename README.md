# Module Extractor

A production-quality Python project that implements an Agentic AI system to extract modules and submodules from help documentation websites.

## Project Overview

This system uses multiple specialized AI agents to:
1. Crawl documentation websites (internal links only)
2. Clean and extract meaningful content
3. Chunk content into manageable pieces
4. Infer modules and submodules using LLM (Llama-3 via Groq API)
5. Deduplicate semantically similar modules
6. Output structured JSON

## Architecture

The system follows an **agentic architecture** where each agent has a single, well-defined responsibility:

### Agents

1. **Crawler Agent** (`agents/crawler_agent.py`)
   - Crawls internal documentation links
   - Avoids infinite loops with visited tracking
   - Respects rate limits with delays
   - Returns raw HTML content

2. **Content Cleaner Agent** (`agents/cleaner_agent.py`)
   - Removes navigation bars, headers, footers
   - Extracts only meaningful content (headings, paragraphs, lists)
   - Preserves semantic structure

3. **Chunking Agent** (`agents/chunking_agent.py`)
   - Splits content into 500-800 token chunks
   - Preserves semantic structure (keeps headings with content)
   - Uses tiktoken for accurate token counting

4. **Module Inference Agent** (`agents/module_agent.py`)
   - Uses LLM (Llama-3) to infer modules and submodules
   - Generates descriptions based on content
   - Avoids hallucination by using only provided content
   - Maintains logical hierarchy

5. **Deduplication Agent** (`agents/dedup_agent.py`)
   - Identifies semantically similar modules
   - Uses similarity comparison and LLM-based reasoning
   - Merges duplicate modules intelligently

### Supporting Components

- **LLM Client** (`api/llm_client.py`): Handles all Groq API interactions
- **HTML Utils** (`utils/html_utils.py`): HTML parsing and link extraction
- **Similarity Utils** (`utils/similarity_utils.py`): Semantic similarity comparison

## How Agentic Design is Used

The agentic architecture provides:

1. **Separation of Concerns**: Each agent handles one specific task
2. **Modularity**: Agents can be tested and modified independently
3. **Scalability**: Easy to add new agents or modify existing ones
4. **Maintainability**: Clear responsibilities make debugging easier
5. **Reusability**: Agents can be reused in different contexts

The agents work in a pipeline:
```
URLs → Crawler → Cleaner → Chunker → Module Inference → Deduplication → JSON Output
```

Each agent processes the output of the previous agent, transforming data step by step.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Groq API key (free at https://console.groq.com/)

### Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Groq API key as an environment variable:

**Option A: Use the provided setup script (Windows):**
```bash
# PowerShell (recommended)
.\setup_api_key.ps1

# Or Command Prompt
setup_api_key.bat
```

**Option B: Set manually:**
```bash
# Windows (PowerShell)
$env:GROQ_API_KEY="your-api-key-here"

# Windows (CMD) - temporary session only
set GROQ_API_KEY=your-api-key-here

# Windows (CMD) - permanent
setx GROQ_API_KEY "your-api-key-here"

# Linux/Mac
export GROQ_API_KEY="your-api-key-here"
```

**Get your free Groq API key at:** https://console.groq.com/

## How to Run Streamlit App

1. Navigate to the module_extractor directory:
```bash
cd module_extractor
```

2. Ensure your GROQ_API_KEY is set (see Setup Instructions above)

3. Run Streamlit:
```bash
streamlit run app.py
```

**Note**: Make sure you're running from within the `module_extractor` directory, not from the parent directory.

3. Open your browser to the URL shown (usually http://localhost:8501)

4. Enter one or more documentation URLs (one per line)

5. Click "Extract Modules"

6. View the JSON output and download if needed

## Output Format

The system outputs a strict JSON format:

```json
[
  {
    "module": "Module Name",
    "Description": "Clear description of the module",
    "Submodules": {
      "Submodule 1": "Description",
      "Submodule 2": "Description"
    }
  }
]
```

## Limitations

1. **API Rate Limits**: Groq API has rate limits. Large documentation sites may require multiple runs.

2. **Token Limits**: LLM has token limits. Very large documentation sites are chunked, but extremely large sites may need multiple passes.

3. **Internal Links Only**: The crawler only follows internal links. External documentation links are ignored.

4. **Content Quality**: Extraction quality depends on the structure and quality of the source documentation.

5. **Language**: Currently optimized for English documentation.

6. **LLM Hallucination**: While prompts are designed to prevent hallucination, the LLM may occasionally infer modules not explicitly stated.

## Assumptions

1. **Documentation Structure**: Assumes documentation has some structure (headings, sections, etc.)

2. **HTML Format**: Assumes documentation is served as HTML (not PDF, Markdown files, etc.)

3. **Accessibility**: Assumes documentation pages are publicly accessible (no authentication required)

4. **Groq API Availability**: Assumes Groq API is available and accessible

5. **Network**: Assumes stable internet connection for crawling and API calls

## Project Structure

```
module_extractor/
│
├── app.py                    # Streamlit UI
├── api/
│   └── llm_client.py        # Groq API client
│
├── agents/
│   ├── crawler_agent.py     # Web crawler
│   ├── cleaner_agent.py     # HTML cleaner
│   ├── chunking_agent.py    # Content chunker
│   ├── module_agent.py      # Module inference
│   └── dedup_agent.py       # Deduplication
│
├── utils/
│   ├── html_utils.py        # HTML utilities
│   └── similarity_utils.py  # Similarity functions
│
├── output/
│   └── sample_output.json   # Example output
│
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Code Quality Features

- **Type Hints**: Used throughout for better code clarity
- **Error Handling**: Comprehensive error handling in all agents
- **Modular Functions**: Each function has a single responsibility
- **Clear Comments**: Well-documented code
- **Clean Naming**: Descriptive variable and function names
- **No Unused Code**: Only necessary code included

## Example Usage

```python
from module_extractor.agents.crawler_agent import CrawlerAgent
from module_extractor.agents.cleaner_agent import CleanerAgent
from module_extractor.agents.chunking_agent import ChunkingAgent
from module_extractor.agents.module_agent import ModuleAgent
from module_extractor.agents.dedup_agent import DedupAgent
from module_extractor.api.llm_client import GroqLLMClient

# Initialize
llm_client = GroqLLMClient()
crawler = CrawlerAgent()
cleaner = CleanerAgent()
chunker = ChunkingAgent()
module_agent = ModuleAgent(llm_client)
dedup_agent = DedupAgent(llm_client)

# Process
urls = ["https://docs.example.com"]
pages = crawler.crawl(urls)
cleaned = cleaner.clean(pages)
chunks = chunker.chunk(cleaned)
modules = module_agent.infer_modules(chunks)
final_modules = dedup_agent.deduplicate(modules)

print(json.dumps(final_modules, indent=2))
```

## License

This project is created for educational/assignment purposes.

