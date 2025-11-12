## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Python 3.11+ for local development

## Step 1: Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name CampusReports \
  --attribute-definitions \
    AttributeName=building,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=building,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Step 2: Set Up IAM Role for Lambda

1. Create a trust policy file `trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

2. Create the role:
```bash
aws iam create-role \
  --role-name CampusFlowLambdaRole \
  --assume-role-policy-document file://trust-policy.json
```

3. Attach policies:
```bash
# Basic Lambda execution
aws iam attach-role-policy \
  --role-name CampusFlowLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# DynamoDB access
aws iam attach-role-policy \
  --role-name CampusFlowLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Bedrock access
aws iam attach-role-policy \
  --role-name CampusFlowLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

## Step 3: Enable Bedrock Model Access

1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access to "Anthropic Claude 3 Sonnet"
4. Wait for approval (usually instant)

## Step 4: Create Lambda Function

1. Package the function:
```bash
cd backend
./deploy.sh
```

2. Or create manually:
```bash
cd backend
zip -r lambda-deployment.zip *.py
pip install -r requirements.txt -t .
zip -r lambda-deployment.zip . -x "*.pyc" -x "__pycache__/*"

aws lambda create-function \
  --function-name campusflow-process-report \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/CampusFlowLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    DYNAMODB_TABLE_NAME=CampusReports,
    AWS_REGION=us-east-1,
    BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
  }" \
  --region us-east-1
```

## Step 5: Create API Gateway

1. Create REST API:
```bash
aws apigateway create-rest-api \
  --name CampusFlowAPI \
  --description "CampusFlow API Gateway" \
  --region us-east-1
```

2. Note the API ID from the response

3. Create resources and methods (use AWS Console for easier setup):
   - `/report` (POST)
   - `/reports` (GET)
   - `/trends` (GET)

4. Deploy the API:
```bash
aws apigateway create-deployment \
  --rest-api-id YOUR_API_ID \
  --stage-name prod \
  --region us-east-1
```

5. Get the API Gateway URL:
```bash
echo "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod"
```

## Step 6: Configure Environment Variables

Update `.env` file in the project root:
```
API_GATEWAY_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=CampusReports
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## Step 7: Test Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run Streamlit app:
```bash
streamlit run frontend/app.py
```

## Troubleshooting

### Lambda Timeout
- Increase timeout: `aws lambda update-function-configuration --function-name campusflow-process-report --timeout 60`

### Bedrock Access Denied
- Ensure model access is granted in Bedrock console
- Check IAM role has `bedrock:InvokeModel` permission

### DynamoDB Errors
- Verify table exists: `aws dynamodb describe-table --table-name CampusReports`
- Check IAM role has DynamoDB permissions

### API Gateway CORS
- Ensure CORS is enabled in API Gateway settings
- Check Lambda returns proper CORS headers

## Cost Estimation

- **DynamoDB**: Pay-per-request, ~$0.25 per million requests
- **Lambda**: First 1M requests free, then $0.20 per million
- **Bedrock**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **API Gateway**: First 1M requests free, then $3.50 per million

Estimated monthly cost for moderate usage: **$5-15**


