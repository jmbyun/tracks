import os
import urllib.parse
import urllib.request
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from ...vault import vault
from ...config import settings
from ...secret import secret

# In local development, allow HTTP for oauthlib
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

INSTAGRAM_CLIENT_ID = secret.get("INSTAGRAM_CLIENT_ID")
INSTAGRAM_CLIENT_SECRET = secret.get("INSTAGRAM_CLIENT_SECRET")

router = APIRouter(prefix="/api/connection/instagram", tags=["connection"])

# Basic display scopes for Instagram
SCOPES = ["user_profile", "user_media"]

def get_redirect_uri():
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/api/connection/instagram/callback"

@router.get("/auth-url")
def get_auth_url(request: Request):
    if not INSTAGRAM_CLIENT_ID or not INSTAGRAM_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="Instagram client credentials not configured. Please add INSTAGRAM_CLIENT_ID and INSTAGRAM_CLIENT_SECRET to secret.py"
        )

    redirect_uri = get_redirect_uri()
    
    # State token to prevent CSRF
    state = os.urandom(16).hex()
    vault.set("INSTAGRAM_OAUTH_STATE", state)
    
    # Construct the authorization URL
    params = {
        'client_id': INSTAGRAM_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ','.join(SCOPES),
        'response_type': 'code',
        'state': state
    }
    
    auth_url = f"https://api.instagram.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    return {"auth_url": auth_url}

@router.get("/callback")
def instagram_callback(request: Request, state: str = None, code: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {error} - {error_description}")
        
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
        
    saved_state = vault.get("INSTAGRAM_OAUTH_STATE")
    if saved_state and state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    redirect_uri = get_redirect_uri()
    
    # 1. Exchange the authorization code for a short-lived access token
    token_url = "https://api.instagram.com/oauth/access_token"
    token_data = urllib.parse.urlencode({
        'client_id': INSTAGRAM_CLIENT_ID,
        'client_secret': INSTAGRAM_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(token_url, data=token_data, method='POST')
        with urllib.request.urlopen(req) as response:
            short_lived_result = json.loads(response.read().decode('utf-8'))
            short_lived_token = short_lived_result.get('access_token')
            user_id = short_lived_result.get('user_id')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise HTTPException(status_code=400, detail=f"Failed to fetch short-lived token: {error_body}")
        
    # 2. Exchange short-lived token for a long-lived token (60 days)
    if short_lived_token:
        long_lived_url = "https://graph.instagram.com/access_token"
        ll_params = urllib.parse.urlencode({
            'grant_type': 'ig_exchange_token',
            'client_secret': INSTAGRAM_CLIENT_SECRET,
            'access_token': short_lived_token
        })
        
        try:
            with urllib.request.urlopen(f"{long_lived_url}?{ll_params}") as response:
                long_lived_result = json.loads(response.read().decode('utf-8'))
                long_lived_token = long_lived_result.get('access_token')
                
                # Save to vault
                if long_lived_token:
                    vault.set("INSTAGRAM_OAUTH_TOKEN", long_lived_token)
                if user_id:
                    vault.set("INSTAGRAM_USER_ID", str(user_id))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Failed to upgrade to long-lived token: {error_body}")
            # Fallback to short-lived if upgrade fails
            vault.set("INSTAGRAM_OAUTH_TOKEN", short_lived_token)
            if user_id:
                vault.set("INSTAGRAM_USER_ID", str(user_id))
    
    # Make sure we clean up the one-time state
    vault.delete("INSTAGRAM_OAUTH_STATE")
        
    # Redirect user back to connections page on frontend
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections")

@router.delete("/remove")
def remove_instagram_connection():
    vault.delete("INSTAGRAM_OAUTH_TOKEN")
    vault.delete("INSTAGRAM_USER_ID")
    return {"status": "success"}
