"""
Authentication module supporting both API keys and OAuth for LLM providers.

Supported auth methods:
- api_key: Traditional API key authentication
- oauth: OAuth2 flow for providers that support it

OAuth is supported for:
- Google (Gemini) - Full OAuth2 support
- Azure OpenAI - Azure AD OAuth
- xAI - OAuth via X/Twitter account (if available)
"""
import os
import json
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Token storage path
TOKEN_DIR = Path.home() / ".evoswarm" / "tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)


def get_token_path(provider: str) -> Path:
    return TOKEN_DIR / f"{provider}_token.json"


def save_token(provider: str, token_data: dict):
    """Save OAuth token to disk."""
    token_data["saved_at"] = datetime.now().isoformat()
    with open(get_token_path(provider), "w") as f:
        json.dump(token_data, f)


def load_token(provider: str) -> Optional[dict]:
    """Load OAuth token from disk if valid."""
    path = get_token_path(provider)
    if not path.exists():
        return None
    
    with open(path) as f:
        token_data = json.load(f)
    
    # Check if token is expired
    if "expires_at" in token_data:
        expires = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() >= expires:
            return None  # Token expired
    
    return token_data


def get_auth_method(provider: str) -> str:
    """Get configured auth method for provider."""
    return os.getenv(f"{provider.upper()}_AUTH_METHOD", "api_key")


# ─────────────────────────────────────────────
# Google OAuth (Gemini)
# ─────────────────────────────────────────────

def google_oauth_flow():
    """Run Google OAuth2 flow for Gemini API access."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        raise ImportError("Install google-auth-oauthlib: pip install google-auth-oauthlib")
    
    SCOPES = ["https://www.googleapis.com/auth/generative-language"]
    
    # Check for existing token
    token_data = load_token("google")
    if token_data:
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_token("google", json.loads(creds.to_json()))
            return creds
    
    # Need new auth flow
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError(
            "For Google OAuth, set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env\n"
            "Get them from: https://console.cloud.google.com/apis/credentials"
        )
    
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080)
    
    save_token("google", json.loads(creds.to_json()))
    return creds


def get_google_credentials():
    """Get Google credentials (OAuth or API key)."""
    auth_method = get_auth_method("google")
    
    if auth_method == "oauth":
        return {"credentials": google_oauth_flow()}
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Set GOOGLE_API_KEY in .env or use GOOGLE_AUTH_METHOD=oauth")
        return {"google_api_key": api_key}


# ─────────────────────────────────────────────
# OpenAI / Azure OpenAI OAuth
# ─────────────────────────────────────────────

def azure_openai_oauth_flow():
    """Get Azure AD token for Azure OpenAI."""
    try:
        from azure.identity import InteractiveBrowserCredential, DeviceCodeCredential
    except ImportError:
        raise ImportError("Install azure-identity: pip install azure-identity")
    
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    
    if not tenant_id:
        raise ValueError("Set AZURE_TENANT_ID for Azure OAuth")
    
    # Try browser auth first, fall back to device code
    try:
        credential = InteractiveBrowserCredential(tenant_id=tenant_id, client_id=client_id)
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
    except Exception:
        credential = DeviceCodeCredential(tenant_id=tenant_id, client_id=client_id)
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    return token.token


def get_openai_credentials():
    """Get OpenAI credentials (API key or Azure OAuth)."""
    auth_method = get_auth_method("openai")
    
    if auth_method == "oauth" or auth_method == "azure":
        # Azure OpenAI with OAuth
        token = azure_openai_oauth_flow()
        return {
            "api_key": token,
            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_type": "azure_ad",
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        }
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Set OPENAI_API_KEY in .env or use OPENAI_AUTH_METHOD=oauth for Azure")
        return {"api_key": api_key}


# ─────────────────────────────────────────────
# Anthropic (API key only for now)
# ─────────────────────────────────────────────

def get_anthropic_credentials():
    """Get Anthropic credentials (API key only)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Set ANTHROPIC_API_KEY in .env")
    return {"api_key": api_key}


# ─────────────────────────────────────────────
# xAI / Grok OAuth (via X account)
# ─────────────────────────────────────────────

def xai_oauth_flow():
    """OAuth flow for xAI via X (Twitter) account."""
    try:
        import requests
        from requests_oauthlib import OAuth2Session
    except ImportError:
        raise ImportError("Install requests-oauthlib: pip install requests-oauthlib")
    
    client_id = os.getenv("XAI_CLIENT_ID")
    client_secret = os.getenv("XAI_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError(
            "For xAI OAuth, set XAI_CLIENT_ID and XAI_CLIENT_SECRET in .env\n"
            "Get them from: https://console.x.ai/api-keys"
        )
    
    # Check for existing token
    token_data = load_token("xai")
    if token_data and "access_token" in token_data:
        # Check if still valid
        expires_at = token_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
            return token_data["access_token"]
    
    # OAuth2 flow
    authorization_base_url = "https://api.x.ai/oauth/authorize"
    token_url = "https://api.x.ai/oauth/token"
    redirect_uri = "http://localhost:8080/callback"
    
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=["api.read", "api.write"])
    authorization_url, state = oauth.authorization_url(authorization_base_url)
    
    print(f"\nOpen this URL to authorize xAI:\n{authorization_url}\n")
    webbrowser.open(authorization_url)
    
    # Simple local server to catch the callback
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    auth_code = None
    
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            auth_code = params.get("code", [None])[0]
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorized! You can close this window.</h1>")
        
        def log_message(self, format, *args):
            pass  # Suppress logging
    
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()
    
    if not auth_code:
        raise ValueError("Failed to get authorization code")
    
    # Exchange code for token
    token = oauth.fetch_token(
        token_url,
        code=auth_code,
        client_secret=client_secret,
    )
    
    # Save token
    token_data = {
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "expires_at": (datetime.now() + timedelta(seconds=token.get("expires_in", 3600))).isoformat(),
    }
    save_token("xai", token_data)
    
    return token["access_token"]


def get_xai_credentials():
    """Get xAI credentials (API key or OAuth)."""
    auth_method = get_auth_method("xai")
    
    if auth_method == "oauth":
        token = xai_oauth_flow()
        return {"api_key": token}
    else:
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("Set XAI_API_KEY in .env or use XAI_AUTH_METHOD=oauth")
        return {"api_key": api_key}


# ─────────────────────────────────────────────
# Main credential getter
# ─────────────────────────────────────────────

def get_credentials(provider: str) -> dict:
    """Get credentials for the specified provider."""
    provider = provider.lower()
    
    if provider == "openai":
        return get_openai_credentials()
    elif provider == "anthropic":
        return get_anthropic_credentials()
    elif provider == "google":
        return get_google_credentials()
    elif provider == "xai":
        return get_xai_credentials()
    else:
        return {}  # Ollama doesn't need credentials
