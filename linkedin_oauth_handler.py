import os
import json
import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class LinkedInOAuthHandler:
    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 redirect_uri: str,
                 token_path: str = 'assets/linkedin_tokens.json'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_path = token_path
        self.token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.token_data = self._load_tokens()

    def _load_tokens(self) -> Dict[str, Any]:
        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_tokens(self, data: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
        with open(self.token_path, 'w') as f:
            json.dump(data, f, indent=2)

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.token_url, data=data, headers=headers)
            resp.raise_for_status()
            token_data = resp.json()
            # Calculate expiry
            expires_in = token_data.get('expires_in', 0)
            token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in - 60)).isoformat()
            self._save_tokens(token_data)
            self.token_data = token_data
            return token_data

    async def refresh_access_token(self) -> Dict[str, Any]:
        refresh_token = self.token_data.get('refresh_token')
        if not refresh_token:
            raise Exception('No refresh token available')
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.token_url, data=data, headers=headers)
            resp.raise_for_status()
            token_data = resp.json()
            expires_in = token_data.get('expires_in', 0)
            token_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=expires_in - 60)).isoformat()
            # Keep refresh_token if not returned
            if 'refresh_token' not in token_data:
                token_data['refresh_token'] = refresh_token
            self._save_tokens(token_data)
            self.token_data = token_data
            return token_data

    def _is_token_expired(self) -> bool:
        expires_at = self.token_data.get('expires_at')
        if not expires_at:
            return True
        return datetime.utcnow() >= datetime.fromisoformat(expires_at)

    async def get_valid_access_token(self) -> Optional[str]:
        print(f"DEBUG: token_data keys: {list(self.token_data.keys())}")
        print(f"DEBUG: access_token exists: {'access_token' in self.token_data}")
        print(f"DEBUG: expires_at: {self.token_data.get('expires_at')}")
        
        if not self.token_data.get('access_token'):
            print("DEBUG: No access token found")
            return None
            
        if self._is_token_expired():
            print("DEBUG: Token is expired, trying to refresh")
            try:
                await self.refresh_access_token()
            except Exception as e:
                print(f"DEBUG: Failed to refresh token: {str(e)}")
                return None
        else:
            print("DEBUG: Token is valid")
            
        return self.token_data.get('access_token') 