# CampusFlow 🏛️

A real-time campus insight platform helping students and staff discover quiet spaces, report issues instantly, and understand campus well-being: powered by AWS Bedrock and Claude 3.

## Features

- 🗺️ **Interactive Campus Map**: Visual representation of buildings with color-coded status
  - 🔵 Blue = Quiet
  - 🟠 Orange = Busy  
  - 🔴 Red = Broken/Issues
- 📊 **Real-time Issue Reporting**: Students and staff can report problems (e.g., broken outlets, lighting issues, accessibility concerns) in seconds.
- 🤖 **AI-Powered Insights**: AWS Bedrock (Claude 3) analyzes reports to summarize trends, recurring issues, and peak hours.
- ♿ **Accessibility Features**: View wheelchair-accessible entrances and facilities
- 📈 **Trend Analysis**: Displays aggregated metrics: top buildings with issues, most reported problems, and improvement over time.

## Architecture

```
┌─────────────────┐
│  Streamlit UI   │
│  (Frontend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Lambda         │─────▶│  DynamoDB    │
│  (Process       │      │  (Storage)   │
│   Reports)      │      └──────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bedrock        │
│  (Claude 3)     │
└─────────────────┘
```

## Project Structure

```
campusflow/
├── frontend/
│   ├── app.py              # Main Streamlit application
│   ├── map_utils.py        # Map rendering utilities
│   └── api_client.py       # API Gateway client
├── backend/
│   ├── lambda_function.py  # Lambda handler
│   ├── bedrock_client.py   # Bedrock AI integration
│   └── dynamodb_client.py  # DynamoDB operations
├── data/
│   ├── buildings.json      # Building data
│   ├── occupancy.json     # Mock occupancy data
│   └── accessibility.json # Accessibility features
├── infrastructure/
│   ├── deploy.sh          # Deployment script
│   └── terraform/         # Infrastructure as code (optional)
└── requirements.txt
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- AWS Account with access to:
  - Lambda
  - DynamoDB
  - Bedrock (Claude 3 access)
  - API Gateway
- AWS CLI configured with credentials

### Local Development

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and region
   ```

3. **Create DynamoDB table:**
   ```bash
   aws dynamodb create-table \
     --table-name CampusReports \
     --attribute-definitions \
       AttributeName=building,AttributeType=S \
       AttributeName=timestamp,AttributeType=S \
     --key-schema \
       AttributeName=building,KeyType=HASH \
       AttributeName=timestamp,KeyType=RANGE \
     --billing-mode PAY_PER_REQUEST
   ```

4. **Deploy Lambda function:**
   ```bash
   cd backend
   ./deploy.sh
   ```

5. **Run Streamlit app:**
   ```bash
   streamlit run frontend/app.py
   ```

### AWS Setup

See `infrastructure/README.md` for detailed AWS setup instructions.

## Usage

1. **View Campus Map**: Open the app to see building statuses
2. **Report Issues**: Click "Report Issue" and fill out the form
3. **View Trends**: Click "Show Trends" to see AI-generated summaries
4. **Accessibility**: Click "View Accessibility" to see accessible features

## License

MIT


