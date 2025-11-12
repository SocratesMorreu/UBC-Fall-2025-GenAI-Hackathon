"""
AI API Client for integrating with Claude or ChatGPT
Supports OpenAI GPT and Anthropic Claude APIs
"""
import os
import json
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()


class AIClient:
    """Client for OpenAI GPT or Anthropic Claude API"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.use_openai = bool(self.openai_api_key)
        self.use_anthropic = bool(self.anthropic_api_key)
        
        # Default to OpenAI if both are available, otherwise use whichever is available
        if self.use_openai:
            self.provider = "openai"
        elif self.use_anthropic:
            self.provider = "anthropic"
        else:
            self.provider = None
    
    def chat(self, user_query: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """
        Send a chat request to AI API
        
        Args:
            user_query: User's question
            context: Additional context (e.g., building data, occupancy info)
            system_prompt: System prompt to guide the AI
        
        Returns:
            AI-generated response
        """
        if not self.provider:
            return None  # No API configured, return None to use local chatbot
        
        if self.provider == "openai":
            return self._chat_openai(user_query, context, system_prompt)
        elif self.provider == "anthropic":
            return self._chat_anthropic(user_query, context, system_prompt)
        
        return None
    
    def _chat_openai(self, user_query: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Chat using OpenAI GPT API"""
        try:
            # Build messages
            messages = []
            
            # System prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system",
                    "content": """You are a helpful campus AI assistant for UBC (University of British Columbia). 
You help students with:
- Finding study spots based on real-time occupancy
- Building recommendations and navigation
- Accessibility information
- Campus services (dining, registration, etc.)
- General student questions

Be friendly, detailed, and provide comprehensive answers. Use emojis appropriately. 
If you have real-time data (occupancy, building status), use it to give specific recommendations."""
                })
            
            # Add context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Additional context: {context}"
                })
            
            # User query
            messages.append({"role": "user", "content": user_query})
            
            # Call OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # or "gpt-3.5-turbo" for cheaper option
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def _chat_anthropic(self, user_query: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Chat using Anthropic Claude API"""
        try:
            # Build system prompt
            if not system_prompt:
                system_prompt = """You are a helpful campus AI assistant for UBC (University of British Columbia). 
You help students with:
- Finding study spots based on real-time occupancy
- Building recommendations and navigation
- Accessibility information
- Campus services (dining, registration, etc.)
- General student questions

Be friendly, detailed, and provide comprehensive answers. Use emojis appropriately. 
If you have real-time data (occupancy, building status), use it to give specific recommendations."""
            
            # Add context if provided
            if context:
                system_prompt += f"\n\nAdditional context: {context}"
            
            # Call Anthropic API
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",  # or "claude-3-haiku-20240307" for faster/cheaper
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_query}
                    ]
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return None

