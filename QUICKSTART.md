# CampusFlow Quick Start Guide

How to get CampusFlow running in 5 minutes!

## Option 1: Local Development (No AWS Required)

Perfect for testing the UI and frontend functionality.

### Steps:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit app:**
   ```bash
   streamlit run frontend/app.py
   ```

3. **Open your browser:**
   - The app will open at `http://localhost:8501`
   - You can interact with the map and UI
   - Reports will use mock data (no AWS connection needed)

## Option 2: Full AWS Setup

For production use with real AI summarization and data storage.

### Prerequisites:
- AWS account
- AWS CLI configured (`aws configure`)
- Python 3.9+

### Steps:

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

2. **Create DynamoDB table:**
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

3. **Enable Bedrock access:**
   - Go to AWS Console → Bedrock → Model access
   - Request access to "Anthropic Claude 3 Sonnet"

4. **Deploy Lambda function:**
   ```bash
   cd infrastructure
   ./deploy.sh
   ```
   Or follow the detailed guide in `infrastructure/README.md`

5. **Set up API Gateway:**
   - Follow instructions in `infrastructure/README.md`
   - Update `.env` with your API Gateway URL

6. **Run the app:**
   ```bash
   streamlit run frontend/app.py
   ```

## Testing the Application

### Demo Flow:

1. **View Map:**
   - Open the app
   - See buildings with color-coded status
   - Blue = Quiet, Orange = Busy, Red = Broken

2. **Report an Issue:**
   - Click "Report Issue" button
   - Select building (e.g., "IKB")
   - Choose issue type (e.g., "outlet")
   - Enter description: "Outlets not working on 3rd floor"
   - Submit

3. **View Trends:**
   - Click "Show Trends" button
   - See AI-generated summary of today's issues
   - View top 3 issues by building

4. **Accessibility:**
   - Check "View Accessibility" checkbox
   - See wheelchair-accessible entrances on map
   - View accessibility details in sidebar

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Map not displaying
- Check that `folium` and `streamlit-folium` are installed
- Try refreshing the browser

### API connection errors
- Verify `.env` file has correct `API_GATEWAY_URL`
- Check AWS credentials are configured
- Ensure Lambda function is deployed

### Bedrock errors
- Verify Bedrock model access is enabled
- Check IAM role has Bedrock permissions
- Ensure correct model ID in `.env`

## Next Steps

- Customize building data in `data/buildings.json`
- Add more buildings or adjust coordinates
- Modify AI prompts in `backend/bedrock_client.py`
- Deploy to production following `infrastructure/README.md`

## Support

For detailed setup instructions, see:
- `README.md` - Project overview
- `infrastructure/README.md` - AWS setup guide


