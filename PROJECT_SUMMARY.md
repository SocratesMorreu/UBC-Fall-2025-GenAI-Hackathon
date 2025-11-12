# ubica (CampusFlow) - Project Summary

## ✅ What's Been Built

### 🎨 Frontend (Streamlit)
- **Interactive Campus Map** 
  - Folium-based map with building markers
  - Clickable markers with building information
  - Layer control for street / light / dark / satellite tiles
  - Wayfinder routing (start → destination) with distance + walk time
  - Predictive flow panel surfaced under the map

- **User Interface Features**
  - Conversational GenAI assistant (local logic + Claude/GPT optional)
  - "Report Issue" button with photo upload + mock S3
  - Accessibility toggle for wheelchair entrances
  - Predictive occupancy selector (Morning/Midday/Afternoon/Evening)
  - Wayfinder sidebar controls (From/To)
  - Live summary report counts + hotspots

- **Components**
- `frontend/app.py` - Main Streamlit application / predictive UI / wayfinder
- `frontend/map_utils.py` - Map rendering utilities (routing, layers)
- `frontend/api_client.py` - API Gateway & Bedrock client (with mock + Claude/GPT)

### 🧠 Backend (AWS Lambda + Bedrock + GPT optional)
- **Lambda Function** (`backend/lambda_function.py`)
  - Handles report submission (POST /report)
  - Retrieves reports (GET /reports)
  - Generates trends (GET /trends)
  - Full CORS support

- **AI Integration** (`backend/bedrock_client.py`, `frontend/ai_api_client.py`)
  - Claude 3 Sonnet integration via AWS Bedrock (real-time summarization + classification)
  - Optional OpenAI GPT integration through a shared client
  - Local fallback logic (no external API required)

- **Data Layer** (`backend/dynamodb_client.py`)
  - DynamoDB operations
  - Report storage and retrieval
  - Today's reports filtering

### 📊 Data Files
- `data/buildings.json` - Building locations, status, amenities (28 entries)
- `data/accessibility.json` - Wheelchair entrances, elevator counts, notes
- `data/issues.json` - Sample issue backlog feeding trends & summary cards
- `data/predictions.json` - Time-slot forecasts for predictive flow
- `data/occupancy.json` - Mock occupancy data (legacy)

### ☁️ Infrastructure
- `infrastructure/deploy.sh` - Lambda deployment script
- `infrastructure/README.md` - Complete AWS setup guide
- `backend/test_local.py` - Local testing utilities


### Option 1: Local Only (No AWS)
```bash
pip install -r requirements.txt
streamlit run frontend/app.py
```
Works with mock data - perfect for UI testing!

### Option 2: Full AWS Setup
1. Follow `QUICKSTART.md` or `infrastructure/README.md`
2. Set up DynamoDB, Lambda, API Gateway, Bedrock
3. Configure `.env` file
4. Run: `streamlit run frontend/app.py`

## 📁 Project Structure

```
campusflow/
├── frontend/
│   ├── app.py              # Main Streamlit app
│   ├── map_utils.py        # Map rendering
│   └── api_client.py       # API client
├── backend/
│   ├── lambda_function.py  # Lambda handler
│   ├── bedrock_client.py   # AI integration
│   ├── dynamodb_client.py  # Database operations
│   └── test_local.py       # Testing utilities
├── data/
│   ├── buildings.json      # Building data
│   ├── accessibility.json  # Accessibility info
│   └── occupancy.json      # Occupancy data
├── infrastructure/
│   ├── deploy.sh           # Deployment script
│   └── README.md           # AWS setup guide
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── run.sh                 # Quick start script
├── README.md              # Project overview
├── QUICKSTART.md          # Quick start guide
└── PROJECT_SUMMARY.md     # This file
```

## 🔧 Key Features Implemented

✅ Interactive campus map with Folium
✅ Wayfinder routing overlay
✅ Predictive flow planner (time-slot forecasts)
✅ Conversational GenAI (Claude/GPT optional)
✅ Report issue form with S3/photo mock
✅ Accessibility overlay
✅ AI-generated trends (mock + real)
✅ Real-time data visualization
✅ AWS Lambda integration
✅ DynamoDB storage
✅ Bedrock Claude 3 AI
✅ Optional OpenAI GPT integration
✅ API Gateway ready
✅ Mock mode for local development
✅ CORS support
✅ Error handling