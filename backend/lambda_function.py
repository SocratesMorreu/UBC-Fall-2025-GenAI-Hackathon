"""
AWS Lambda function for processing campus reports
Handles report submission, retrieval, and AI summarization
"""
import json
import os
from datetime import datetime

from dynamodb_client import DynamoDBClient
from bedrock_client import BedrockClient

# Initialize clients
dynamodb_client = DynamoDBClient()
bedrock_client = BedrockClient()

def lambda_handler(event, context):
    """
    Lambda handler for API Gateway requests
    
    Expected event structure:
    {
        "httpMethod": "GET" | "POST",
        "path": "/report" | "/reports" | "/trends",
        "body": {...} (for POST requests),
        "queryStringParameters": {...} (for GET requests)
    }
    """
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # Handle OPTIONS request (CORS preflight)
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({})
            }
        
        # Route requests
        if path == '/report' and http_method == 'POST':
            return handle_submit_report(event, headers)
        elif path == '/reports' and http_method == 'GET':
            return handle_get_reports(event, headers)
        elif path == '/trends' and http_method == 'GET':
            return handle_get_trends(event, headers)
        elif path == '/chat' and http_method == 'POST':
            return handle_chat(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def handle_submit_report(event, headers):
    """Handle report submission"""
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        building = body.get('building')
        issue_type = body.get('issue_type', 'other')
        description = body.get('description', '')
        severity = body.get('severity', 'medium')
        photo_url = body.get('photo_url')  # S3 URL if photo was uploaded
        
        # Validate required fields
        if not building or not description:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required fields: building and description'
                })
            }
        
        # Optionally classify the report using AI
        if issue_type == 'other' or not issue_type:
            issue_type = bedrock_client.classify_report(description)
        
        # Store report in DynamoDB
        result = dynamodb_client.put_report(
            building=building,
            photo_url=photo_url,
            issue_type=issue_type,
            description=description,
            severity=severity
        )
        
        return {
            'statusCode': result.get('statusCode', 200),
            'headers': headers,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_get_reports(event, headers):
    """Handle report retrieval"""
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        building = query_params.get('building')
        
        # Retrieve reports
        reports = dynamodb_client.get_reports(building=building)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(reports)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_get_trends(event, headers):
    """Handle trends/summary retrieval"""
    try:
        # Get today's reports
        reports = dynamodb_client.get_reports_today()
        
        # Generate AI summary
        summary = bedrock_client.summarize_reports(reports)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(summary)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_chat(event, headers):
    """Handle chatbot queries"""
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        user_query = body.get('query', '')
        
        if not user_query:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required field: query'
                })
            }
        
        # Load buildings and accessibility data
        buildings = load_buildings_data()
        accessibility_data = load_accessibility_data()
        
        # Generate AI response
        response_text = bedrock_client.chat_recommendation(
            user_query=user_query,
            buildings=buildings,
            accessibility_data=accessibility_data
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response_text,
                'query': user_query
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def load_buildings_data():
    """Load buildings data - in production, this would come from a database"""
    # Try to load from file if available (for local testing)
    try:
        from pathlib import Path
        # Get the parent directory (project root)
        project_root = Path(__file__).parent.parent
        buildings_path = project_root / 'data' / 'buildings.json'
        
        if buildings_path.exists():
            with open(buildings_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Fallback: return mock data structure
    return [
        {
            "id": "ikb",
            "name": "Irving K. Barber Learning Centre",
            "lat": 49.2606,
            "lon": -123.2460,
            "status": "busy",
            "occupancy": 85,
            "capacity": 100
        }
    ]

def load_accessibility_data():
    """Load accessibility data - in production, this would come from a database"""
    # Try to load from file if available (for local testing)
    try:
        from pathlib import Path
        # Get the parent directory (project root)
        project_root = Path(__file__).parent.parent
        accessibility_path = project_root / 'data' / 'accessibility.json'
        
        if accessibility_path.exists():
            with open(accessibility_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Fallback: return empty list
    return []


