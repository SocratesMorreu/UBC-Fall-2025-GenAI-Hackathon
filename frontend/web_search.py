"""
Web search integration for AI chatbot
Provides real-world data and web search capabilities
"""
import os
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()


class WebSearch:
    """Web search integration using DuckDuckGo or SerpAPI"""
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY", "")
        self.use_serpapi = bool(self.serpapi_key)
    
    def search(self, query: str, num_results: int = 3) -> List[Dict]:
        """
        Search the web for information
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            List of search results with title, snippet, and link
        """
        if self.use_serpapi:
            return self._search_serpapi(query, num_results)
        else:
            # Use DuckDuckGo as fallback (no API key needed)
            return self._search_duckduckgo(query, num_results)
    
    def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        """Search using SerpAPI (requires API key)"""
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google",
                "num": num_results
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for item in data["organic_results"][:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", "")
                    })
            return results
        except Exception as e:
            print(f"SerpAPI search error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo (no API key required)"""
        try:
            # Use DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "snippet": data.get("AbstractText", ""),
                    "link": data.get("AbstractURL", "")
                })
            
            # Get related topics
            if data.get("RelatedTopics"):
                for topic in data["RelatedTopics"][:num_results-1]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                            "snippet": topic.get("Text", ""),
                            "link": topic.get("FirstURL", "")
                        })
            
            return results[:num_results]
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    def get_weather(self, location: str = "Vancouver, BC") -> Optional[str]:
        """Get weather information for a location"""
        try:
            query = f"weather {location}"
            results = self.search(query, num_results=1)
            if results:
                return results[0].get("snippet", f"Weather information for {location}")
            return None
        except Exception:
            return None
    
    def get_general_info(self, query: str) -> Optional[str]:
        """Get general information about a topic"""
        try:
            results = self.search(query, num_results=2)
            if results:
                info = "\n\n".join([
                    f"**{r['title']}**\n{r['snippet']}"
                    for r in results
                ])
                return info
            return None
        except Exception:
            return None

