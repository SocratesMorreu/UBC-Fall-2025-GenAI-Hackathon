"""
Amazon Polly Text-to-Speech Client
"""
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError

class PollyClient:
    def __init__(self):
        """Initialize Polly client"""
        try:
            self.polly = boto3.client(
                'polly',
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
            )
            self.available = True
        except (NoCredentialsError, Exception):
            self.polly = None
            self.available = False
    
    def synthesize_speech(self, text: str, voice_id: str = "Joanna"):
        """Convert text to speech"""
        if not self.available or not text.strip():
            return None
            
        try:
            clean_text = self._clean_text(text)
            response = self.polly.synthesize_speech(
                Text=clean_text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural'
            )
            return response['AudioStream'].read()
        except Exception as e:
            print(f"Polly error: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean text for speech"""
        text = text.replace('**', '').replace('*', '').replace('_', '')
        text = text.replace('&', 'and').replace('@', 'at').replace('%', 'percent')
        if len(text) > 2900:
            text = text[:2900] + "..."
        return text.strip()