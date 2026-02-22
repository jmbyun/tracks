import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import google_auth_oauthlib.flow

from ...vault import vault
from ...config import settings
from ...secret import secret

# In local development, allow HTTP for oauthlib
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

YOUTUBE_CLIENT_ID = secret.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = secret.get("YOUTUBE_CLIENT_SECRET")


router = APIRouter(prefix="/api/connection/youtube", tags=["connection"])

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def get_client_config():
    return {
        "web": {
            "client_id": YOUTUBE_CLIENT_ID,
            "project_id": "tracks",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": YOUTUBE_CLIENT_SECRET,
        }
    }

@router.get("/auth-url")
def get_auth_url(request: Request):
    if not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="YouTube client credentials not configured. Please add YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET to secret.py"
        )

    redirect_uri = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/api/connection/youtube/callback"
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        get_client_config(), scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    vault.set("YOUTUBE_OAUTH_STATE", state)
    
    return {"auth_url": auth_url}

@router.get("/callback")
def youtube_callback(request: Request, state: str = None, code: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
        
    redirect_uri = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/api/connection/youtube/callback"
    
    saved_state = vault.get("YOUTUBE_OAUTH_STATE")
    if saved_state and state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
        
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        get_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    
    authorization_response = str(request.url)
    
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {str(e)}")
        
    credentials = flow.credentials
    
    if credentials.token:
        vault.set("YOUTUBE_OAUTH_TOKEN", credentials.token)
    if credentials.refresh_token:
        vault.set("YOUTUBE_REFRESH_TOKEN", credentials.refresh_token)
    
    # Make sure we clean up the one-time state
    vault.delete("YOUTUBE_OAUTH_STATE")
        
    # Redirect user back to connections page on frontend
    return RedirectResponse(url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections")

@router.delete("/remove")
def remove_youtube_connection():
    vault.delete("YOUTUBE_OAUTH_TOKEN")
    vault.delete("YOUTUBE_REFRESH_TOKEN")
    return {"status": "success"}
