import os
import urllib.parse
import urllib.request
import json
import base64
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from ...vault import vault
from ...config import settings
from ...secret import secret

SMARTTHINGS_CLIENT_ID = secret.get("SMARTTHINGS_CLIENT_ID")
SMARTTHINGS_CLIENT_SECRET = secret.get("SMARTTHINGS_CLIENT_SECRET")

router = APIRouter(prefix="/api/connection/smartthings", tags=["connection"])

# SmartThings required scopes
SCOPES = ["r:locations:*", "r:devices:*", "x:devices:*"]

def get_redirect_uri():
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/api/connection/smartthings/callback"

@router.get("/auth-url")
def get_auth_url(request: Request):
    if not SMARTTHINGS_CLIENT_ID or not SMARTTHINGS_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="SmartThings client credentials not configured. Please add SMARTTHINGS_CLIENT_ID and SMARTTHINGS_CLIENT_SECRET to secret.py"
        )

    redirect_uri = get_redirect_uri()
    
    # State token to prevent CSRF
    state = os.urandom(16).hex()
    
    # Save state to vault temporarily
    vault.set("SMARTTHINGS_OAUTH_STATE", state)
    
    # Construct the authorization URL
    params = {
        'response_type': 'code',
        'client_id': SMARTTHINGS_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'state': state
    }
    
    auth_url = f"https://api.smartthings.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    return {"auth_url": auth_url}

@router.get("/callback")
def smartthings_callback(request: Request, state: str = None, code: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {error} - {error_description}")
        
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
        
    saved_state = vault.get("SMARTTHINGS_OAUTH_STATE")
    
    if not saved_state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    redirect_uri = get_redirect_uri()
    
    # Exchange the authorization code for an access token
    token_url = "https://api.smartthings.com/oauth/token"
    token_data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'client_id': SMARTTHINGS_CLIENT_ID,
        'client_secret': SMARTTHINGS_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'code': code
    }).encode('utf-8')
    
    # SmartThings requires Basic Auth header with Client ID and Secret, similar to Twitter
    client_creds = f"{SMARTTHINGS_CLIENT_ID}:{SMARTTHINGS_CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f'Basic {encoded_creds}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    try:
        req = urllib.request.Request(token_url, data=token_data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            token_result = json.loads(response.read().decode('utf-8'))
            
            # Save tokens to vault
            access_token = token_result.get('access_token')
            refresh_token = token_result.get('refresh_token')
            
            if access_token:
                vault.set("SMARTTHINGS_OAUTH_TOKEN", access_token)
            if refresh_token:
                vault.set("SMARTTHINGS_REFRESH_TOKEN", refresh_token)
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise HTTPException(status_code=400, detail=f"Failed to fetch SmartThings token: {error_body}")
    
    finally:
        # Clean up the one-time state
        vault.delete("SMARTTHINGS_OAUTH_STATE")
        
    # Redirect user back to connections page on frontend
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections")

@router.post("/webhook")
async def smartthings_webhook(request: Request):
    """
    Handle SmartThings WebApp Lifecycle Events (like CONFIRMATION).
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    lifecycle = body.get("lifecycle")
    
    if lifecycle == "CONFIRMATION":
        confirmation_data = body.get("confirmationData", {})
        confirmation_url = confirmation_data.get("confirmationUrl")
        
        if confirmation_url:
            print(f"[SmartThings] Received CONFIRMATION request. Verifying URL: {confirmation_url}")
            try:
                # Automatically verify the URL by making a GET request
                req = urllib.request.Request(confirmation_url, method="GET")
                with urllib.request.urlopen(req) as response:
                    print(f"[SmartThings] Verified successfully (HTTP {response.status})")
            except Exception as e:
                print(f"[SmartThings] Verification failed: {e}")
                
        return {"targetUrl": settings.SERVER_BASE_URL + "/api/connection/smartthings/webhook"}

    elif lifecycle == "CONFIGURATION":
        return {
            "configurationData": {
                "initialize": {
                    "name": "Tracks App",
                    "description": "Tracks SmartThings Integration",
                    "id": "tracks-app-1",
                    "permissions": ["r:devices:*", "x:devices:*", "r:locations:*"],
                    "firstPageId": "1"
                },
                "page": {
                    "pageId": "1",
                    "name": "Tracks Setup",
                    "nextPageId": None,
                    "previousPageId": None,
                    "complete": True,
                    "sections": []
                }
            }
        }
    
    # Return 200 OK for other lifecycle events (INSTALL, UPDATE, UNINSTALL, OAUTH_CALLBACK)
    return {}

@router.delete("/remove")
def remove_smartthings_connection():
    vault.delete("SMARTTHINGS_OAUTH_TOKEN")
    vault.delete("SMARTTHINGS_REFRESH_TOKEN")
    return {"status": "success"}
