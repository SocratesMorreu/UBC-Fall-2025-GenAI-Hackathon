"""
API Client for communicating with AWS API Gateway
"""
import os
import requests
import json
import boto3
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class APIClient:
    def __init__(self):
        self.api_url = os.getenv("API_GATEWAY_URL", "")
        self.s3_bucket = os.getenv("S3_BUCKET_NAME", "")
        self.timeout = 10
        # Initialize S3 client if bucket is configured
        if self.s3_bucket:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
    
    def upload_photo(self, file, building_id: str) -> Optional[str]:
        """
        Upload photo to S3 bucket
        
        Args:
            file: File object from Streamlit file uploader
            building_id: Building ID for organizing files
        
        Returns:
            S3 URL of uploaded file, or None if upload fails
        """
        if not self.s3_bucket or not self.s3_client:
            # Mock mode - return a mock URL
            return f"mock_s3://{self.s3_bucket}/{building_id}/{file.name}"
        
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/{building_id}/{timestamp}_{file.name}"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file,
                self.s3_bucket,
                filename,
                ExtraArgs={'ContentType': file.type}
            )
            
            # Return S3 URL
            return f"s3://{self.s3_bucket}/{filename}"
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    def submit_report(self, building: str, issue_type: str, description: str, severity: str = "medium", photo_url: Optional[str] = None) -> Dict:
        """
        Submit a new issue report to the API Gateway
        
        Args:
            building: Building ID
            issue_type: Type of issue (e.g., "outlet", "accessibility", "crowd")
            description: Description of the issue
            severity: Severity level (low, medium, high)
        
        Returns:
            Response dictionary from API
        """
        if not self.api_url:
            # Mock response for local development
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Report submitted (mock mode)",
                    "building": building,
                    "issue_type": issue_type
                })
            }
        
        payload = {
            "building": building,
            "issue_type": issue_type,
            "description": description,
            "severity": severity
        }
        
        if photo_url:
            payload["photo_url"] = photo_url
        
        try:
            response = requests.post(
                f"{self.api_url}/report",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "statusCode": 500
            }
    
    def get_reports(self, building: Optional[str] = None) -> List[Dict]:
        """
        Fetch reports from the API
        
        Args:
            building: Optional building ID to filter by
        
        Returns:
            List of reports
        """
        if not self.api_url:
            # Mock data for local development
            return [
                {
                    "building": "ikb",
                    "issue_type": "outlet",
                    "description": "Outlets not working on 3rd floor",
                    "severity": "high",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            ]
        
        try:
            url = f"{self.api_url}/reports"
            if building:
                url += f"?building={building}"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []
    
    def get_trends(self) -> Dict:
        """
        Get AI-generated trends summary
        
        Returns:
            Dictionary with trends summary
        """
        if not self.api_url:
            # Mock summary for local development
            return {
                "summary": "Top 3 issues today: 1) Outlet failures in IKB (5 reports), 2) High occupancy at NEST (3 reports), 3) Accessibility concerns at Scarfe (2 reports)",
                "top_issues": [
                    {"building": "ikb", "issue_type": "outlet", "count": 5},
                    {"building": "nest", "issue_type": "crowd", "count": 3},
                    {"building": "scarfe", "issue_type": "accessibility", "count": 2}
                ]
            }
        
        try:
            response = requests.get(f"{self.api_url}/trends", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "summary": "Unable to fetch trends. Please check API connection.",
                "top_issues": []
            }
    
    def chat(self, query: str) -> str:
        """
        Send a query to the AI chatbot
        
        Args:
            query: User's question/request
        
        Returns:
            AI-generated response
        """
        # Use local AI chatbot first (works without AWS, avoids 403 errors)
        try:
            from ai_chatbot import LocalAIChatbot
            chatbot = LocalAIChatbot()
            return chatbot.chat(query)
        except ImportError:
            # If local chatbot module not found, try API
            pass
        except Exception as e:
            # If local chatbot fails, try API
            pass
        
        # Fallback to API if local chatbot unavailable
        if self.api_url:
            try:
                response = requests.post(
                    f"{self.api_url}/chat",
                    json={"query": query},
                    timeout=30  # Longer timeout for AI responses
                )
                response.raise_for_status()
                result = response.json()
                return result.get('response', 'I apologize, but I could not generate a response.')
            except requests.exceptions.RequestException as e:
                # If API also fails, return basic fallback
                pass
        
        # Final fallback responses
        if "study spot" in query.lower() or "study" in query.lower():
            return "Based on current occupancy, I recommend:\n1. **Scarfe Building** - 20% occupied, quiet status\n2. **Chemistry Building** - 30% occupied, quiet status\n3. **Forestry Sciences Centre** - 25% occupied, quiet status\n\nThese buildings have low occupancy and are great for studying!"
        elif "accessible" in query.lower() or "lift" in query.lower() or "elevator" in query.lower():
            return "Here are buildings with accessible lifts:\n\n1. **Irving K. Barber Learning Centre** - 3 elevators, 4 accessible washrooms\n2. **Koerner Library** - 4 elevators, 6 accessible washrooms\n3. **Sauder School of Business** - 5 elevators, 8 accessible washrooms\n\nAll these buildings have multiple elevators and are fully accessible."
        else:
            return "I can help you find study spots, accessible buildings, and answer questions about campus facilities. Try asking me to 'find me a study spot' or 'where are accessible lifts'."


