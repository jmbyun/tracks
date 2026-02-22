import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAuthHeaders } from '../auth'
import './ConnectionsPage.css'

function ConnectionsPage() {
    const navigate = useNavigate()
    const [vault, setVault] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [message, setMessage] = useState({ text: '', type: '' })

    useEffect(() => {
        fetchVault()
    }, [])

    const fetchVault = async () => {
        setIsLoading(true)
        try {
            const res = await fetch('/api/settings/vault', { headers: getAuthHeaders() })
            if (res.ok) {
                setVault(await res.json())
            }
        } catch (e) {
            console.error('Vault fetch failed:', e)
            showStatus('Failed to load connections status', 'error')
        } finally {
            setIsLoading(false)
        }
    }

    const showStatus = (text, type) => {
        setMessage({ text, type })
        setTimeout(() => setMessage({ text: '', type: '' }), 3000)
    }

    const handleConnectGoogle = async () => {
        try {
            const res = await fetch('/api/connection/google/auth-url', {
                headers: getAuthHeaders()
            })
            if (res.ok) {
                const data = await res.json()
                if (data.auth_url) {
                    window.location.href = data.auth_url
                }
            } else {
                const err = await res.json()
                showStatus(err.detail || 'Failed to initialize Google login', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('Failed to connect to Google', 'error')
        }
    }

    const handleRemoveGoogle = async () => {
        if (!confirm('Are you sure you want to remove the Google connection?')) return
        try {
            const res = await fetch('/api/connection/google/remove', {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                showStatus('Google connection removed', 'success')
                fetchVault()
            } else {
                showStatus('Failed to remove Google connection', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('An error occurred during removal', 'error')
        }
    }

    const isGoogleConnected = vault.some(v => v.key === 'GOOGLE_OAUTH_REFRESH_TOKEN')

    if (isLoading) {
        return <div className="connections-loading">Loading connections...</div>
    }

    return (
        <div className="settings-page">
            <div className="settings-container">
                <header className="settings-header">
                    <h1>Connections</h1>
                    {message.text && (
                        <div className={`status-message ${message.type}`}>
                            {message.text}
                        </div>
                    )}
                </header>

                <section className="settings-section">
                    <h2>Manage Third-Party Integrations</h2>
                    <p className="connections-description" style={{ color: '#a0a0b0', marginBottom: '1.5rem' }}>
                        Connect your external services to enable advanced agent features.
                    </p>

                    <div className="vault-list">
                        <div className="vault-item">
                            <div className="vault-info">
                                <span className="vault-key" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem' }}>
                                    <i className="fa fa-google" style={{ color: '#4ea8de', fontSize: '1.3rem' }}></i> GMail (IMAP/SMTP)
                                </span>
                                <span className="vault-value">
                                    <span className={`status-badge ${isGoogleConnected ? 'on' : 'off'}`}>
                                        {isGoogleConnected ? 'Connected' : 'Not Connected'}
                                    </span>
                                </span>
                            </div>
                            <div className="vault-actions">
                                {isGoogleConnected ? (
                                    <button className="delete-button" onClick={handleRemoveGoogle} title="Remove Connection">
                                        <i className="fa fa-unlink"></i> Disconnect
                                    </button>
                                ) : (
                                    <button className="edit-button" style={{ backgroundColor: '#4ea8de', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleConnectGoogle} title="Connect">
                                        <i className="fa fa-link"></i> Connect
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    )
}

export default ConnectionsPage
