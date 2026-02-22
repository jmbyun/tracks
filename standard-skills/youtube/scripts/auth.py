import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

class YouTubeAuth:
    """
    Handles Google OAuth token management and refresh specifically for YouTube APIs,
    using only the standard library.
    """
    def __init__(self):
        self.client_id = os.environ.get("YOUTUBE_CLIENT_ID")
        self.client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        self.access_token = os.environ.get("YOUTUBE_OAUTH_TOKEN")
        self.refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
        self.api_key = os.environ.get("API_KEY")
        self.server_port = os.environ.get("TRACKS_SERVER_PORT", "8540")
        
        if not all([self.client_id, self.client_secret, self.api_key]):
            raise ValueError("Missing required YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, or API_KEY environment variables.")

    def get_token(self):
        """
        Returns a valid access token. Tests it, and if it fails, attempts a refresh.
        """
        if self._is_token_valid(self.access_token):
            return self.access_token
            
        if not self.refresh_token:
            raise ValueError("Missing YOUTUBE_REFRESH_TOKEN. Please connect your YouTube account via the Tracks settings dashboard.")
            
        # Try a refresh using google endpoint
        new_tokens = self._refresh_access_token()
        new_access = new_tokens.get("access_token")
        
        if not new_access:
            raise ValueError("Failed to refresh access token, please reconnect YouTube from the Settings dashboard.")
            
        self.access_token = new_access
        self._save_to_vault("YOUTUBE_OAUTH_TOKEN", new_access)
            
        return self.access_token

    def _is_token_valid(self, token):
        if not token:
            return False
            
        # Basic request to check token validity
        req = urllib.request.Request("https://oauth2.googleapis.com/tokeninfo?access_token=" + token)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception:
            return False

    def _refresh_access_token(self):
        """Refreshes a Google OAuth token"""
        url = "https://oauth2.googleapis.com/token"
        
        data = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise ValueError(f"Failed to refresh YouTube token: HTTP {e.code} - {error_body}")
            
    def _save_to_vault(self, key, value):
        """Saves a value back to the Tracks application vault via the API"""
        url = f"http://localhost:{self.server_port}/api/settings/vault/{key}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({"key": key, "value": value}).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
            with urllib.request.urlopen(req) as response:
                if response.status not in (200, 201):
                    raise ValueError(f"Failed to save {key}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                post_url = f"http://localhost:{self.server_port}/api/settings/vault"
                post_req = urllib.request.Request(post_url, data=data, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(post_req) as post_response:
                        pass
                except Exception as inner_e:
                    print(f"Failed to save {key} to vault: {inner_e}")
            else:
                print(f"Failed to save {key} to vault: HTTP {e.code}")


def make_youtube_request(endpoint, method="GET", data=None):
    """
    Helper function to make a standard REST API call to YouTube Data API v3
    using the automatically refreshed tokens.
    """
    auth = YouTubeAuth()
    token = auth.get_token()
    
    base_url = "https://www.googleapis.com/youtube/v3"
    url = f"{base_url}/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                return {} # No content
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"YouTube API Error (HTTP {e.code}): {error_body}")
