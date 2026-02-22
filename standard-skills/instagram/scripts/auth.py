import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

class InstagramAuth:
    """
    Handles Instagram API authentication and token refresh using only the standard library.
    """
    def __init__(self):
        self.client_id = os.environ.get("INSTAGRAM_CLIENT_ID")
        self.client_secret = os.environ.get("INSTAGRAM_CLIENT_SECRET")
        self.token = os.environ.get("INSTAGRAM_OAUTH_TOKEN")
        self.user_id = os.environ.get("INSTAGRAM_USER_ID")
        self.api_key = os.environ.get("API_KEY")
        self.server_port = os.environ.get("TRACKS_SERVER_PORT", "8540")
        
        if not all([self.client_id, self.client_secret, self.token, self.api_key]):
            raise ValueError("Missing required Instagram OAuth or API Key environment variables.")

    def get_token(self):
        """
        Returns a valid access token. Tests it, and if it fails, attempts a refresh.
        """
        if self._is_token_valid(self.token):
            # Optimistically try to refresh long-lived tokens in the background
            # Instagram allows long-lived tokens to be refreshed if they are at least 24h old.
            # For simplicity in standard scripts, if it's valid, we just use it.
            return self.token
            
        # Try a refresh using the standard Graph API refresh endpoint
        new_token_data = self._refresh_access_token()
        new_token = new_token_data.get("access_token")
        if not new_token:
            raise ValueError("Failed to refresh access token, please reconnect Instagram from the Settings dashboard.")
            
        self.token = new_token
        self._save_to_vault("INSTAGRAM_OAUTH_TOKEN", new_token)
            
        return self.token

    def _is_token_valid(self, token):
        if not token:
            return False
            
        # Basic request to check token validity
        req = urllib.request.Request(f"https://graph.instagram.com/v19.0/me?fields=id&access_token={token}")
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception:
            return False

    def _refresh_access_token(self):
        """Refreshes a long-lived Instagram token using Graph API"""
        url = "https://graph.instagram.com/refresh_access_token"
        params = urllib.parse.urlencode({
            'grant_type': 'ig_refresh_token',
            'access_token': self.token
        })
        
        req = urllib.request.Request(f"{url}?{params}")
        
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


def make_instagram_request(endpoint, method="GET", data=None):
    """
    Helper function to make a standard REST API call to Instagram Graph API
    using the automatically refreshed tokens.
    """
    auth = InstagramAuth()
    token = auth.get_token()
    
    # Prepend graph API base path
    base_url = "https://graph.instagram.com/v19.0"
    url = f"{base_url}/{endpoint}"
    
    # Append access token to query params
    if "?" in url:
        url += f"&access_token={token}"
    else:
        url += f"?access_token={token}"
    
    headers = {
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
        raise Exception(f"Instagram API Error (HTTP {e.code}): {error_body}")
