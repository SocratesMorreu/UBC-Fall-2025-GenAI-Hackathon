"""
DynamoDB Stream Lambda Function for AI Trend Detection
Automatically detects trends when new reports are added to DynamoDB
"""
import json
import boto3
from datetime import datetime, timedelta
from collections import defaultdict
from bedrock_client import BedrockClient

dynamodb = boto3.resource('dynamodb')
bedrock_client = BedrockClient()

def lambda_handler(event, context):
    """
    Process DynamoDB stream events and detect trends
    
    Triggered when new reports are inserted into DynamoDB
    If 5+ reports of same type in 30 mins → auto-notify admin
    """
    print(f"Received {len(event['Records'])} stream records")
    
    # Process stream records
    new_reports = []
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_item = record['dynamodb']['NewImage']
            report = {
                'building': new_item.get('building', {}).get('S', ''),
                'issue_type': new_item.get('issue_type', {}).get('S', ''),
                'description': new_item.get('description', {}).get('S', ''),
                'severity': new_item.get('severity', {}).get('S', ''),
                'timestamp': new_item.get('timestamp', {}).get('S', '')
            }
            new_reports.append(report)
    
    if not new_reports:
        return {'statusCode': 200, 'body': 'No new reports to process'}
    
    # Get all recent reports (last 30 minutes)
    table = dynamodb.Table('CampusFlowReports')
    thirty_min_ago = (datetime.utcnow() - timedelta(minutes=30)).isoformat() + 'Z'
    
    try:
        # Scan for recent reports (in production, use GSI with timestamp)
        response = table.scan(
            FilterExpression='timestamp >= :time',
            ExpressionAttributeValues={':time': thirty_min_ago}
        )
        recent_reports = response.get('Items', [])
    except Exception as e:
        print(f"Error fetching recent reports: {e}")
        recent_reports = []
    
    # Group reports by building and issue type
    report_groups = defaultdict(list)
    for report in recent_reports:
        key = f"{report.get('building', 'unknown')}_{report.get('issue_type', 'unknown')}"
        report_groups[key].append(report)
    
    # Check for trends (5+ reports of same type in 30 mins)
    alerts = []
    for key, reports in report_groups.items():
        if len(reports) >= 5:
            building, issue_type = key.split('_', 1)
            alerts.append({
                'building': building,
                'issue_type': issue_type,
                'count': len(reports),
                'time_window': '30 minutes',
                'severity': 'high'
            })
    
    # Generate AI summary if alerts found
    if alerts:
        ai_summary = generate_ai_alert_summary(alerts, recent_reports)
        
        # Send notification (SNS, email, etc.)
        send_admin_notification(alerts, ai_summary)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'alerts': alerts,
                'ai_summary': ai_summary,
                'message': 'Trends detected and admin notified'
            })
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'No significant trends detected',
            'reports_processed': len(new_reports)
        })
    }

def generate_ai_alert_summary(alerts, recent_reports):
    """
    Use Bedrock AI to generate a summary of detected trends
    """
    try:
        # Prepare context for AI
        alert_text = "\n".join([
            f"- {alert['building']}: {alert['count']} reports of '{alert['issue_type']}' in last 30 minutes"
            for alert in alerts
        ])
        
        prompt = f"""You are a campus facilities management AI. Analyze these recent issue reports and provide a concise summary.

Recent Alerts:
{alert_text}

Recent Reports Summary:
- Total reports in last 30 minutes: {len(recent_reports)}
- Most common issue types: {get_most_common_issues(recent_reports)}

Provide:
1. A brief summary of the trend
2. Recommended action items
3. Priority level (low/medium/high)

Keep response under 200 words."""

        summary = bedrock_client.generate_text(prompt)
        return summary
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        return "AI summary unavailable. Multiple reports detected - manual review recommended."

def get_most_common_issues(reports):
    """Get most common issue types from reports"""
    issue_counts = defaultdict(int)
    for report in reports:
        issue_type = report.get('issue_type', 'unknown')
        issue_counts[issue_type] += 1
    
    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    return ", ".join([f"{issue}({count})" for issue, count in sorted_issues[:3]])

def send_admin_notification(alerts, ai_summary):
    """
    Send notification to admin (SNS, email, etc.)
    In production, this would send to SNS topic or SES
    """
    try:
        sns = boto3.client('sns')
        topic_arn = 'arn:aws:sns:us-east-1:123456789012:campusflow-alerts'  # Configure in env
        
        message = f"""
🚨 CampusFlow Alert: Trend Detected

{alerts[0]['count']} reports of '{alerts[0]['issue_type']}' in {alerts[0]['building']} in the last 30 minutes.

AI Analysis:
{ai_summary}

        """
        
        # Uncomment in production:
        # sns.publish(
        #     TopicArn=topic_arn,
        #     Subject='CampusFlow: Trend Alert',
        #     Message=message
        # )
        
        print(f"Notification prepared: {message}")
    except Exception as e:
        print(f"Error sending notification: {e}")

