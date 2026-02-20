/**
 * Authentication utility for API key management.
 */

const API_KEY_STORAGE_KEY = 'tracks_api_key'

export function getApiKey() {
    return localStorage.getItem(API_KEY_STORAGE_KEY) || ''
}

export function setApiKey(key) {
    localStorage.setItem(API_KEY_STORAGE_KEY, key)
}

export function clearApiKey() {
    localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function getAuthHeaders() {
    const apiKey = getApiKey()
    if (!apiKey) return {}
    return { 'Authorization': `Bearer ${apiKey}` }
}

/**
 * Validate the stored API key against the backend.
 * Returns true if valid, false otherwise.
 */
export async function validateApiKey(apiKey) {
    try {
        const response = await fetch('/api/heartbeat/status', {
            headers: { 'Authorization': `Bearer ${apiKey}` }
        })
        return response.ok
    } catch {
        return false
    }
}
