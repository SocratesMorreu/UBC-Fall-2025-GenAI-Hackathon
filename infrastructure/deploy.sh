#!/bin/bash

# Deployment script for CampusFlow Lambda function
# This script packages and deploys the Lambda function to AWS

set -e

echo "🚀 Deploying CampusFlow Lambda function..."

# Configuration
FUNCTION_NAME="campusflow-process-report"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="CampusFlowLambdaRole"

# Create deployment package
echo "📦 Creating deployment package..."
cd "$(dirname "$0")/../backend"
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy function code
cp *.py package/

# Create ZIP file
cd package
zip -r ../lambda-deployment.zip .
cd ..
rm -rf package

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "📝 Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file fileb://lambda-deployment.zip \
        --region "$REGION"
else
    echo "⚠️  Function does not exist. Please create it first using AWS Console or CLI."
    echo "   You'll need to:"
    echo "   1. Create an IAM role with Lambda execution permissions"
    echo "   2. Create the Lambda function with:"
    echo "      aws lambda create-function \\"
    echo "        --function-name $FUNCTION_NAME \\"
    echo "        --runtime $RUNTIME \\"
    echo "        --role arn:aws:iam::YOUR_ACCOUNT:role/$ROLE_NAME \\"
    echo "        --handler $HANDLER \\"
    echo "        --zip-file fileb://lambda-deployment.zip \\"
    echo "        --region $REGION"
fi

# Clean up
rm -f lambda-deployment.zip

echo "✅ Deployment complete!"


