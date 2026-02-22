import os
import urllib.parse
import urllib.request
import json
import base64
import hashlib
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from ...vault import vault
from ...config import settings
from ...secret import secret

# In local development, allow HTTP for oauthlib
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

TWITTER_CLIENT_ID = secret.get("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = secret.get("TWITTER_CLIENT_SECRET")

router = APIRouter(prefix="/api/connection/twitter", tags=["connection"])

# Twitter required scopes for V2 API
SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]

def get_redirect_uri():
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/api/connection/twitter/callback"

def generate_pkce_verifier(length=128):
    """Generate a random PKCE code verifier."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8').rstrip('=')

def generate_pkce_challenge(verifier):
    """Generate a PKCE code challenge from the verifier."""
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

@router.get("/auth-url")
def get_auth_url(request: Request):
    if not TWITTER_CLIENT_ID or not TWITTER_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="Twitter client credentials not configured. Please add TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET to secret.py"
        )

    redirect_uri = get_redirect_uri()
    
    # State token to prevent CSRF
    state = os.urandom(16).hex()
    
    # Generate PKCE parameters
    code_verifier = generate_pkce_verifier()
    code_challenge = generate_pkce_challenge(code_verifier)
    
    # Save state and verifier to vault temporarily
    vault.set("TWITTER_OAUTH_STATE", state)
    vault.set("TWITTER_CODE_VERIFIER", code_verifier)
    
    # Construct the authorization URL
    params = {
        'response_type': 'code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urllib.parse.urlencode(params)}"
    
    return {"auth_url": auth_url}

@router.get("/callback")
def twitter_callback(request: Request, state: str = None, code: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {error} - {error_description}")
        
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
        
    saved_state = vault.get("TWITTER_OAUTH_STATE")
    code_verifier = vault.get("TWITTER_CODE_VERIFIER")
    
    if not saved_state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing PKCE code verifier")
        
    redirect_uri = get_redirect_uri()
    
    # Exchange the authorization code for an access token
    token_url = "https://api.twitter.com/2/oauth2/token"
    token_data = urllib.parse.urlencode({
        'client_id': TWITTER_CLIENT_ID,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code,
        'code_verifier': code_verifier
    }).encode('utf-8')
    
    # Twitter requires Basic Auth header with Client ID and Secret
    client_creds = f"{TWITTER_CLIENT_ID}:{TWITTER_CLIENT_SECRET}"
    encoded_creds = base64.b64encode(client_creds.encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f'Basic {encoded_creds}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        req = urllib.request.Request(token_url, data=token_data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            token_result = json.loads(response.read().decode('utf-8'))
            
            # Save tokens to vault
            access_token = token_result.get('access_token')
            refresh_token = token_result.get('refresh_token')
            
            if access_token:
                vault.set("TWITTER_OAUTH_TOKEN", access_token)
            if refresh_token:
                vault.set("TWITTER_REFRESH_TOKEN", refresh_token)
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise HTTPException(status_code=400, detail=f"Failed to fetch Twitter token: {error_body}")
    
    finally:
        # Clean up the one-time state and verifier
        vault.delete("TWITTER_OAUTH_STATE")
        vault.delete("TWITTER_CODE_VERIFIER")
        
    # Redirect user back to connections page on frontend
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections")

@router.delete("/remove")
def remove_twitter_connection():
    vault.delete("TWITTER_OAUTH_TOKEN")
    vault.delete("TWITTER_REFRESH_TOKEN")
    return {"status": "success"}
