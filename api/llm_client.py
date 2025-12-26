"""
LLM Client for Groq API integration with Llama-3 models.

This module handles all interactions with the Groq API, providing
a clean interface for LLM-based operations.
"""

import os
import json
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GroqLLMClient:
    """
    Client for interacting with Groq API using Llama-3 models.
    
    Handles API calls, error handling, and response parsing.
    Uses environment variable GROQ_API_KEY for authentication.
    """
    
    def __init__(self, model: str = "llama-3.1-70b-versatile"):
        """
        Initialize the Groq LLM client.
        
        Args:
            model: Model name to use. Defaults to llama-3.1-70b-versatile.
                   Alternatives: llama-3.1-8b-instant, llama-3-70b-8192
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it before running the application."
            )
        
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _make_request(self, messages: list, temperature: float = 0.1, max_tokens: int = 4000, force_json: bool = False) -> Dict[str, Any]:
        """
        Make a request to the Groq API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
            force_json: If True, request JSON format response (may not be supported by all models)
            
        Returns:
            API response dictionary
            
        Raises:
            Exception: If API request fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add response_format for JSON mode if requested
        if force_json:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = self.session.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Provide more detailed error for HTTP errors
            error_detail = ""
            try:
                error_response = response.json()
                error_detail = f" - {error_response}"
            except:
                error_detail = f" - Status: {response.status_code}, Response: {response.text[:200]}"
            raise Exception(f"Groq API HTTP error: {str(e)}{error_detail}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Groq API request failed: {str(e)}")
    
    def generate_json(self, prompt: str, context: str = "", temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate JSON output from a prompt and optional context.
        
        Args:
            prompt: The main prompt/instruction (content should be embedded in prompt)
            context: DEPRECATED - content should be embedded in prompt instead
            temperature: Sampling temperature (default 0.1 for deterministic output)
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            Exception: If JSON parsing fails or API call fails
        """
        # Use prompt directly - content should already be embedded in prompt
        # Do NOT pass context separately to avoid duplication
        full_prompt = prompt
        
        messages = [
            {
                "role": "system",
                "content": "You are a precise documentation analyzer. Always respond with valid JSON only. Do not include any markdown formatting or code blocks around the JSON."
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ]
        
        try:
            # DO NOT use force_json - Groq doesn't support response_format parameter
            response = self._make_request(messages, temperature=temperature, force_json=False)
            content = response["choices"][0]["message"]["content"]
            
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Validate JSON starts with {
            if not content.startswith("{"):
                raise Exception(f"Invalid JSON response - does not start with {{. Response: {content[:200]}")
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            content_preview = content[:500] if 'content' in locals() else "N/A"
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {content_preview}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {str(e)}")
    
    def generate_text(self, prompt: str, context: str = "", temperature: float = 0.3) -> str:
        """
        Generate plain text output (for non-JSON tasks).
        
        Args:
            prompt: The main prompt/instruction
            context: Optional context text to include
            temperature: Sampling temperature
            
        Returns:
            Generated text string
        """
        if context:
            full_prompt = f"{prompt}\n\nContext:\n{context}"
        else:
            full_prompt = prompt
        
        messages = [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
        
        response = self._make_request(messages, temperature=temperature)
        return response["choices"][0]["message"]["content"].strip()

