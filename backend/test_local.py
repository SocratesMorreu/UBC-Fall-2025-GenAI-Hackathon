"""
Local testing script for Lambda function
Simulates API Gateway events for local development
"""
import json
import os
from lambda_function import lambda_handler

# Set environment variables for local testing
os.environ['DYNAMODB_TABLE_NAME'] = 'CampusReports'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'

def test_submit_report():
    """Test report submission"""
    event = {
        'httpMethod': 'POST',
        'path': '/report',
        'body': json.dumps({
            'building': 'ikb',
            'issue_type': 'outlet',
            'description': 'Outlets not working on 3rd floor',
            'severity': 'high'
        })
    }
    
    context = {}
    response = lambda_handler(event, context)
    print("Submit Report Response:")
    print(json.dumps(response, indent=2))
    return response

def test_get_reports():
    """Test report retrieval"""
    event = {
        'httpMethod': 'GET',
        'path': '/reports',
        'queryStringParameters': None
    }
    
    context = {}
    response = lambda_handler(event, context)
    print("\nGet Reports Response:")
    print(json.dumps(response, indent=2))
    return response

def test_get_trends():
    """Test trends retrieval"""
    event = {
        'httpMethod': 'GET',
        'path': '/trends',
        'queryStringParameters': None
    }
    
    context = {}
    response = lambda_handler(event, context)
    print("\nGet Trends Response:")
    print(json.dumps(response, indent=2))
    return response

if __name__ == '__main__':
    print("🧪 Testing CampusFlow Lambda Function Locally\n")
    print("=" * 50)
    
    # Note: These tests require AWS credentials and actual AWS resources
    # For true local testing, consider using LocalStack or mocks
    
    try:
        test_submit_report()
        test_get_reports()
        test_get_trends()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Local testing requires:")
        print("  1. AWS credentials configured")
        print("  2. DynamoDB table 'CampusReports' exists")
        print("  3. Bedrock model access enabled")


