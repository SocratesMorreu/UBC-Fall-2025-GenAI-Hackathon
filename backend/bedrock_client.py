"""
AWS Bedrock client for AI-powered summarization using Claude 3
"""
import os
import json
import boto3
from typing import Dict, List
from datetime import datetime

class BedrockClient:
    def __init__(self):
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        
        # Initialize Bedrock runtime client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=self.region
        )
    
    def summarize_reports(self, reports: List[Dict]) -> Dict:
        """
        Generate AI summary of campus reports using Claude 3
        
        Args:
            reports: List of report dictionaries
        
        Returns:
            Dictionary with summary and top issues
        """
        if not reports:
            return {
                'summary': 'No reports available for analysis.',
                'top_issues': []
            }
        
        # Prepare prompt
        reports_text = self._format_reports_for_prompt(reports)
        
        prompt = f"""You are analyzing campus facility reports. Summarize the key trends and issues.

Reports:
{reports_text}

Please provide:
1. A concise summary (2-3 sentences) of today's trends across buildings
2. The top 3 issues by frequency and building

Format your response as JSON:
{{
    "summary": "Your summary here",
    "top_issues": [
        {{"building": "building_id", "issue_type": "type", "count": number, "description": "brief description"}},
        ...
    ]
}}

Be factual and concise. Focus on actionable insights."""

        try:
            # Call Claude 3 via Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                text_response = content[0].get('text', '')
                
                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    json_start = text_response.find('{')
                    json_end = text_response.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = text_response[json_start:json_end]
                        result = json.loads(json_str)
                        return result
                    else:
                        # Fallback: return text as summary
                        return {
                            'summary': text_response,
                            'top_issues': self._extract_top_issues(reports)
                        }
                except json.JSONDecodeError:
                    # If JSON parsing fails, return text as summary
                    return {
                        'summary': text_response,
                        'top_issues': self._extract_top_issues(reports)
                    }
            else:
                return {
                    'summary': 'Unable to generate summary.',
                    'top_issues': self._extract_top_issues(reports)
                }
        
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            # Fallback to simple aggregation
            return {
                'summary': f'Analyzed {len(reports)} reports. Unable to generate AI summary due to API error.',
                'top_issues': self._extract_top_issues(reports)
            }
    
    def _format_reports_for_prompt(self, reports: List[Dict]) -> str:
        """Format reports into a readable string for the prompt"""
        formatted = []
        for report in reports:
            building = report.get('building', 'Unknown')
            issue_type = report.get('issue_type', 'Unknown')
            description = report.get('description', 'No description')
            severity = report.get('severity', 'medium')
            timestamp = report.get('timestamp', 'Unknown time')
            
            formatted.append(
                f"- Building: {building}, Type: {issue_type}, "
                f"Severity: {severity}, Description: {description}, Time: {timestamp}"
            )
        
        return '\n'.join(formatted)
    
    def _extract_top_issues(self, reports: List[Dict]) -> List[Dict]:
        """Extract top issues by frequency (fallback method)"""
        from collections import Counter
        
        # Count issues by building and type
        issue_counts = Counter()
        issue_descriptions = {}
        
        for report in reports:
            building = report.get('building', 'unknown')
            issue_type = report.get('issue_type', 'unknown')
            key = f"{building}_{issue_type}"
            
            issue_counts[key] += 1
            if key not in issue_descriptions:
                issue_descriptions[key] = report.get('description', '')[:50]
        
        # Get top 3
        top_issues = []
        for (key, count) in issue_counts.most_common(3):
            building, issue_type = key.split('_', 1)
            top_issues.append({
                'building': building,
                'issue_type': issue_type,
                'count': count,
                'description': issue_descriptions.get(key, '')
            })
        
        return top_issues
    
    def classify_report(self, description: str) -> str:
        """
        Classify an incoming report description into a category
        
        Args:
            description: Report description text
        
        Returns:
            Classified issue type
        """
        prompt = f"""Classify this campus facility report into one of these categories:
- outlet (electrical outlets, charging stations)
- accessibility (wheelchair access, elevators, ramps)
- crowd (occupancy, capacity)
- temperature (heating, cooling, HVAC)
- other (anything else)

Report: "{description}"

Respond with ONLY the category name (one word)."""

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 50,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                classification = content[0].get('text', 'other').strip().lower()
                # Validate classification
                valid_types = ['outlet', 'accessibility', 'crowd', 'temperature', 'other']
                if classification in valid_types:
                    return classification
            
            return 'other'
        
        except Exception as e:
            print(f"Error classifying report: {e}")
            return 'other'
    
    def chat_recommendation(self, user_query: str, buildings: List[Dict], accessibility_data: List[Dict]) -> str:
        """
        Generate AI-powered recommendations based on user query
        
        Args:
            user_query: User's question/request (e.g., "find me a study spot", "where are accessible lifts")
            buildings: List of building dictionaries with occupancy and status
            accessibility_data: List of accessibility information
        
        Returns:
            AI-generated response with recommendations
        """
        # Format building data for context
        buildings_context = []
        for building in buildings:
            occupancy_pct = (building.get('occupancy', 0) / building.get('capacity', 100) * 100) if building.get('capacity', 100) > 0 else 0
            buildings_context.append(
                f"- {building['name']} ({building['id']}): {building.get('status', 'quiet')} status, "
                f"{occupancy_pct:.1f}% occupied ({building.get('occupancy', 0)}/{building.get('capacity', 100)}), "
                f"Location: {building.get('lat', 'N/A')}, {building.get('lon', 'N/A')}"
            )
        
        # Format accessibility data for context
        accessibility_context = []
        for acc in accessibility_data:
            building_name = next((b['name'] for b in buildings if b['id'] == acc['building_id']), acc['building_id'])
            accessibility_context.append(
                f"- {building_name} ({acc['building_id']}): {acc['elevators']} elevators, "
                f"{acc['accessible_washrooms']} accessible washrooms. {acc['notes']}"
            )
        
        prompt = f"""You are a helpful campus assistant for CampusFlow. Answer user questions about study spots, accessibility, and building recommendations.

Campus Buildings Data:
{chr(10).join(buildings_context)}

Accessibility Information:
{chr(10).join(accessibility_context)}

User Query: "{user_query}"

Instructions:
1. If the user asks about study spots, recommend buildings with "quiet" status and low occupancy (<50%)
2. If the user asks about accessibility (lifts, elevators, wheelchair access), provide specific information from the accessibility data
3. Be conversational, helpful, and specific
4. Include building names, occupancy percentages, and any relevant details
5. If asking about distance/location, mention that buildings are on campus
6. Format your response in a friendly, easy-to-read way

Response:"""

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [])
            
            if content and len(content) > 0:
                return content[0].get('text', 'I apologize, but I could not generate a response. Please try rephrasing your question.')
            else:
                return 'I apologize, but I could not generate a response. Please try rephrasing your question.'
        
        except Exception as e:
            print(f"Error in chat recommendation: {e}")
            # Fallback response
            return f"I encountered an error processing your request. Please try again or rephrase your question. Error: {str(e)}"


