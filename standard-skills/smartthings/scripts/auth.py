import os
import json
import urllib.request
import urllib.error
import urllib.parse
import base64

class SmartThingsAuth:
    """
    Handles SmartThings API authentication and token refresh using only the standard library.
    """
    def __init__(self):
        self.client_id = os.environ.get("SMARTTHINGS_CLIENT_ID")
        self.client_secret = os.environ.get("SMARTTHINGS_CLIENT_SECRET")
        self.access_token = os.environ.get("SMARTTHINGS_OAUTH_TOKEN")
        self.refresh_token = os.environ.get("SMARTTHINGS_REFRESH_TOKEN")
        self.api_key = os.environ.get("API_KEY")
        self.server_port = os.environ.get("TRACKS_SERVER_PORT", "8540")
        
        if not all([self.client_id, self.client_secret, self.api_key]):
            raise ValueError("Missing required SMARTTHINGS_CLIENT_ID, SMARTTHINGS_CLIENT_SECRET, or API_KEY environment variables.")

    def get_token(self):
        """
        Returns a valid access token. Tests it, and if it fails, attempts a refresh.
        """
        if self._is_token_valid(self.access_token):
            return self.access_token
            
        if not self.refresh_token:
            raise ValueError("Missing SMARTTHINGS_REFRESH_TOKEN. Please connect your SmartThings account via the Tracks settings dashboard.")
            
        # Try a refresh
        new_tokens = self._refresh_access_token()
        new_access = new_tokens.get("access_token")
        new_refresh = new_tokens.get("refresh_token")
        
        if not new_access:
            raise ValueError("Failed to refresh access token, please reconnect SmartThings from the Settings dashboard.")
            
        self.access_token = new_access
        self.refresh_token = new_refresh
        
        self._save_to_vault("SMARTTHINGS_OAUTH_TOKEN", new_access)
        if new_refresh:
            self._save_to_vault("SMARTTHINGS_REFRESH_TOKEN", new_refresh)
            
        return self.access_token

    def _is_token_valid(self, token):
        if not token:
            return False
            
        # Basic request to check token validity
        req = urllib.request.Request("https://api.smartthings.com/v1/devices?max=1")
        req.add_header('Authorization', f'Bearer {token}')
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception:
            return False

    def _refresh_access_token(self):
        """Refreshes a SmartThings token"""
        url = "https://api.smartthings.com/oauth/token"
        
        client_creds = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(client_creds.encode('utf-8')).decode('utf-8')
        
        data = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }).encode('utf-8')
        
        headers = {
            'Authorization': f'Basic {encoded_creds}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise ValueError(f"Failed to refresh SmartThings token: HTTP {e.code} - {error_body}")
            
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


def make_smartthings_request(endpoint, method="GET", data=None):
    """
    Helper function to make a standard REST API call to SmartThings API
    using the automatically refreshed tokens.
    """
    auth = SmartThingsAuth()
    token = auth.get_token()
    
    base_url = "https://api.smartthings.com/v1"
    url = f"{base_url}/{endpoint}"
    
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
        raise Exception(f"SmartThings API Error (HTTP {e.code}): {error_body}")
