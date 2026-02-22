import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

class GmailAuth:
    """
    Handles Gmail API authentication and token refresh using only the standard library.
    """
    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        self.token = os.environ.get("GOOGLE_OAUTH_TOKEN")
        self.refresh_token = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")
        self.api_key = os.environ.get("API_KEY")
        self.server_port = os.environ.get("TRACKS_SERVER_PORT", "8540")
        
        if not all([self.client_id, self.client_secret, self.refresh_token, self.api_key]):
            raise ValueError("Missing required Google OAuth or API Key environment variables.")

    def get_token(self):
        """
        Returns a valid access token. Always attempts to test it, and if it fails,
        refreshes the token and saves it back to the Vault.
        """
        # Test if token is valid by doing a simple inexpensive API call (e.g., getting own profile)
        if self._is_token_valid(self.token):
            return self.token
            
        # If invalid, refresh it
        new_token_data = self._refresh_access_token()
        new_token = new_token_data.get("access_token")
        if not new_token:
            raise ValueError("Failed to refresh access token: " + str(new_token_data))
            
        self.token = new_token
        self._save_to_vault("GOOGLE_OAUTH_TOKEN", new_token)
        
        # Sometimes a new refresh token is issued
        if "refresh_token" in new_token_data and new_token_data["refresh_token"] != self.refresh_token:
            self.refresh_token = new_token_data["refresh_token"]
            self._save_to_vault("GOOGLE_OAUTH_REFRESH_TOKEN", self.refresh_token)
            
        return self.token

    def _is_token_valid(self, token):
        if not token:
            return False
            
        req = urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/profile")
        req.add_header("Authorization", f"Bearer {token}")
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except urllib.error.HTTPError:
            return False
        except Exception:
            return False

    def _refresh_access_token(self):
        """Refreshes the OAuth token using Google's token endpoint"""
        url = "https://oauth2.googleapis.com/token"
        data = urllib.parse.urlencode({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise ValueError(f"Failed to refresh token: HTTP {e.code} - {error_body}")
            
    def _save_to_vault(self, key, value):
        """Saves a value back to the Tracks application vault via the API"""
        url = f"http://localhost:{self.server_port}/api/settings/vault/{key}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = json.dumps({"key": key, "value": value}).encode('utf-8')
        
        try:
            # First try PUT (update)
            req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
            with urllib.request.urlopen(req) as response:
                if response.status not in (200, 201):
                    raise ValueError(f"Failed to save {key}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # If not found, try POST (create)
                post_url = f"http://localhost:{self.server_port}/api/settings/vault"
                post_req = urllib.request.Request(post_url, data=data, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(post_req) as post_response:
                        if post_response.status not in (200, 201):
                            raise ValueError(f"Failed to save {key} on POST")
                except Exception as inner_e:
                    print(f"Failed to save {key} to vault: {inner_e}")
            else:
                print(f"Failed to save {key} to vault: HTTP {e.code}")

def make_gmail_request(endpoint, method="GET", data=None):
    """
    Helper function to make a standard REST API call to Gmail
    using the automatically refreshed tokens.
    """
    auth = GmailAuth()
    token = auth.get_token()
    
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
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
        raise Exception(f"Gmail API Error (HTTP {e.code}): {error_body}")
