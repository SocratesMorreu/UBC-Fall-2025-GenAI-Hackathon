# AI Chatbot Setup Guide

## API Integration

The chatbot now supports integration with **OpenAI GPT** or **Anthropic Claude** for more intelligent, ChatGPT-like responses.

### Setup Instructions

1. **Create a `.env` file** in the project root (if it doesn't exist)

2. **Add your API key** (choose one):

   **Option A: OpenAI (ChatGPT)**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   **Option B: Anthropic (Claude)**
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. **Get API Keys:**
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Anthropic**: https://console.anthropic.com/

### Features

- **Intelligent Responses**: Uses GPT-4 or Claude for detailed, comprehensive answers
- **Real-time Context**: Includes current building occupancy and campus data
- **Student-focused**: Tailored for university/student questions
- **Fallback**: If no API key is set, uses local intelligent chatbot

### What the AI Can Do

- Answer complex student questions
- Provide detailed study spot recommendations
- Help with registration (Workday)
- Campus navigation and building info
- General knowledge with web search integration

### Notes

- The chatbot will automatically use the API if a key is provided
- Falls back to local logic if API is unavailable
- Web search integration works independently

