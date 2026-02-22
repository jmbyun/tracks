# How to Add a New Third-Party Connection

This guide outlines the standard procedure for integrating a new third-party service (e.g., Slack, Notion, GitHub) into the Tracks agent environment using OAuth 2.0.

By following this pattern, you can quickly say `"ADD_CONNECTION.md 참고해서 Slack 연동해줘"` and the AI will know exactly what components need to be built.

## Overview of Components
To successfully integrate a new service, you need to implement changes across 5 distinct layers of the Tracks application:
1. **Secrets Management**: Storing API Client IDs and Secrets.
2. **Backend Controllers**: Creating the OAuth redirect and callback endpoints.
3. **Frontend UI**: Adding "Connect/Disconnect" buttons on the Settings page.
4. **Agent Clients**: Injecting the acquired tokens into the agent's runtime environment.
5. **Agent Skill**: Writing the standard library Python scripts for the agent to use the service.

---

## 1. Secrets Management
The Developer must create an OAuth App on the target service's developer portal and acquire a `CLIENT_ID` and `CLIENT_SECRET`.

1. Add these keys to the base64-encoded JSON in `tracks/secret.py`.
2. Ensure the redirect URI in the developer portal is set to: `http://localhost:8541/api/connection/<service_name>/callback`.

## 2. Backend Controllers
We use FastAPI for the backend. Create a new file for the service (e.g., `tracks/controllers/connection/<service>.py`).

### Endpoints Required:
- **`GET /auth-url`**: 
  - Generates the OAuth authorization URL using the `CLIENT_ID`.
  - Sets a CSRF `state` parameter in the Vault (`vault.set("<SERVICE>_OAUTH_STATE", state)`).
  - Uses `settings.FRONTEND_BASE_URL` to construct the `redirect_uri`.
- **`GET /callback`**: 
  - Validates the `state` parameter.
  - Exchanges the authorization `code` for an access token (and refresh token) using the `CLIENT_SECRET`.
  - **Crucial:** Saves the resulting tokens directly to the user's `vault.json` using `vault.set("<SERVICE>_OAUTH_TOKEN", token)`.
  - Upgrades short-lived tokens to long-lived tokens if the service supports it (like Instagram).
  - Redirects the user back to the frontend: `RedirectResponse(url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections")`.
- **`DELETE /remove`**: 
  - Removes the tokens from the Vault using `vault.delete()`.

### Routing:
- Register the new router in `tracks/controllers/__init__.py`.
- **Important**: In `tracks/app.py`, add an exception in `verify_api_key()` to skip API Key checks for the `/api/connection/<service>/callback` route (since it's a browser redirect from an external server).

## 3. Frontend UI Updates
The connections page is located at `tracks-web/src/components/ConnectionsPage.jsx`.

1. Add a token existence check: `const isServiceConnected = vault.some(v => v.key === '<SERVICE>_OAUTH_TOKEN')`.
2. Create `handleConnectService` (fetches `/auth-url` and redirects `window.location.href`) and `handleRemoveService` (calls `DELETE /remove`).
3. Add a new `<div className="vault-item">` block in the UI list representing the service, showing either a "Connect" or "Disconnect" button based on the `isConnected` state.

## 4. Agent Clients (Token Injection)
For the LLM agent to actually use the service, it needs the credentials loaded into its environment variables.

1. Open `tracks/clients/codex_client.py` and `tracks/clients/gemini_client.py`.
2. Locate the section where `env` variables are being prepared.
3. Inject the `CLIENT_ID`, `CLIENT_SECRET`, and any required Vault tokens explicitly into the `child_env` / `env` dictionary.

## 5. Agent Skill Creation
Create the tool scripts that the Agent will actually invoke.

1. Use the skill creator: `python standard-skills/skill-creator/scripts/init_skill.py <service> --path standard-skills --resources scripts`.
2. Write a `scripts/auth.py` script that ONLY uses the standard Python library (`urllib.request`). It should:
   - Read the tokens from `os.environ`.
   - Implement an automated Token Refresh logic if the token is expired, and save the updated token back to the Vault via a PUT request to `http://localhost:{server_port}/api/settings/vault/{key}`.
   - Provide a `make_<service>_request()` helper function for the other scripts.
3. Write individual `.py` scripts for every capability (e.g., `list_messages.py`, `post_media.py`). **Do not use third-party libraries like `requests` or official SDKs.**
4. Document the tools thoroughly in `SKILL.md` mentioning how to run the bash scripts, any required pagination or parameters, and their purposes.
5. Run `python standard-skills/skill-creator/scripts/generate_openai_yaml.py standard-skills/<service> --interface ...` to build the UI yaml.

---
*Reference implementations: See `tracks/controllers/connection/google.py`, `tracks/controllers/connection/instagram.py`, and `standard-skills/gmail/*`.*
