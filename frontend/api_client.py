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
from pathlib import Path
from collections import Counter

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
            try:
                issues = self._load_mock_issues()
                timestamp = datetime.utcnow().isoformat() + "Z"
                issue_id = f"ISS-{int(datetime.utcnow().timestamp())}"
                new_issue = {
                    "id": issue_id,
                    "building": building,
                    "issue_type": issue_type,
                    "severity": severity,
                    "status": "open",
                    "reported_at": timestamp,
                    "description": description,
                    "photo_url": photo_url
                }
                issues.append(new_issue)
                self._save_mock_issues(issues)
                return {
                    "statusCode": 200,
                    "issue": new_issue,
                    "message": "Report submitted (local mode)"
                }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "error": f"Unable to write report locally: {e}"
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
            issues = self._load_mock_issues()
            building_lookup = self._load_building_lookup()

            open_issues = [issue for issue in issues if issue.get("status") == "open"]
            if open_issues:
                hotspot_counter = Counter(issue.get("building") for issue in open_issues)
                hotspot_labels = [
                    f"{building_lookup.get(bid, {}).get('name', bid)} ({count})"
                    for bid, count in hotspot_counter.most_common(2)
                ]
                hotspot_text = ", ".join(hotspot_labels) if hotspot_labels else "no hotspots"

                critical_issues = [
                    issue for issue in open_issues if issue.get("severity") == "high"
                ]
                critical_labels = [
                    building_lookup.get(issue.get("building"), {}).get("name", issue.get("building"))
                    for issue in critical_issues
                ]
                critical_text = ", ".join(sorted(set(critical_labels))) or "none"

                summary = (
                    f"{len(open_issues)} open issues across campus. "
                    f"Active hotspots: {hotspot_text}. "
                    f"Critical attention needed at: {critical_text}."
                )

                combo_counter = Counter(
                    (issue.get("building"), issue.get("issue_type"))
                    for issue in open_issues
                )

                top_issues = []
                for (building_id, issue_type), count in combo_counter.most_common(5):
                    top_issues.append({
                        "building": building_id,
                        "issue_type": issue_type,
                        "count": count
                    })

                return {
                    "summary": summary,
                    "top_issues": top_issues
                }
            else:
                return {
                    "summary": "No open reports right now. Campus looks clear!",
                    "top_issues": []
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

    def _load_mock_issues(self) -> List[Dict]:
        path = Path(__file__).parent.parent / "data" / "issues.json"
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_mock_issues(self, issues: List[Dict]) -> None:
        path = Path(__file__).parent.parent / "data" / "issues.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(issues, f, indent=2)

    def _load_building_lookup(self) -> Dict[str, Dict]:
        path = Path(__file__).parent.parent / "data" / "buildings.json"
        try:
            with open(path, "r") as f:
                buildings = json.load(f)
                return {b["id"]: b for b in buildings}
        except FileNotFoundError:
            return {}
    
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


