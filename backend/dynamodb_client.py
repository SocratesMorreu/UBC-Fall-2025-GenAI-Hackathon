"""
DynamoDB client for storing and retrieving campus reports
"""
import os
import boto3
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
import json

class DynamoDBClient:
    def __init__(self):
        self.table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'CampusReports')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)
    
    def put_report(self, building: str, issue_type: str, description: str, severity: str, photo_url: Optional[str] = None) -> Dict:
        """
        Store a new report in DynamoDB
        
        Args:
            building: Building ID
            issue_type: Type of issue
            description: Description of the issue
            severity: Severity level
            photo_url: Optional S3 URL of uploaded photo
        
        Returns:
            Dictionary with operation result
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        report_id = f"{building}_{timestamp}"
        
        item = {
            'building': building,
            'timestamp': timestamp,
            'report_id': report_id,
            'issue_type': issue_type,
            'description': description,
            'severity': severity,
            'status': 'open'
        }
        
        # Add photo URL
        if photo_url:
            item['photo_url'] = photo_url
        
        try:
            self.table.put_item(Item=item)
            return {
                'statusCode': 200,
                'message': 'Report stored successfully',
                'report_id': report_id
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'error': str(e)
            }
    
    def get_reports(self, building: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Retrieve reports from DynamoDB
        
        Args:
            building: Optional building ID to filter by
            limit: Maximum number of reports to return
        
        Returns:
            List of reports
        """
        try:
            if building:
                # Query by building
                response = self.table.query(
                    KeyConditionExpression='building = :building',
                    ExpressionAttributeValues={':building': building},
                    Limit=limit,
                    ScanIndexForward=False  # Most recent first
                )
            else:
                # Scan all reports (use with caution for large tables)
                response = self.table.scan(Limit=limit)
            
            items = response.get('Items', [])
            
            # Convert Decimal to int/float for JSON serialization
            def convert_decimals(obj):
                if isinstance(obj, Decimal):
                    return float(obj) if obj % 1 else int(obj)
                elif isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                return obj
            
            return [convert_decimals(item) for item in items]
        except Exception as e:
            print(f"Error retrieving reports: {e}")
            return []
    
    def get_reports_today(self) -> List[Dict]:
        """
        Get all reports from today
        
        Returns:
            List of today's reports
        """
        today = datetime.utcnow().date().isoformat()
        all_reports = self.get_reports(limit=1000)
        
        # Filter reports from today
        today_reports = [
            report for report in all_reports
            if report.get('timestamp', '').startswith(today)
        ]
        
        return today_reports


