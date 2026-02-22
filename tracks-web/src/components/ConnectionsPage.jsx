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

    const handleConnectInstagram = async () => {
        try {
            const res = await fetch('/api/connection/instagram/auth-url', {
                headers: getAuthHeaders()
            })
            if (res.ok) {
                const data = await res.json()
                if (data.auth_url) {
                    window.location.href = data.auth_url
                }
            } else {
                const err = await res.json()
                showStatus(err.detail || 'Failed to initialize Instagram login', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('Failed to connect to Instagram', 'error')
        }
    }

    const handleConnectTwitter = async () => {
        try {
            const res = await fetch('/api/connection/twitter/auth-url', {
                headers: getAuthHeaders()
            })
            if (res.ok) {
                const data = await res.json()
                if (data.auth_url) {
                    window.location.href = data.auth_url
                }
            } else {
                const err = await res.json()
                showStatus(err.detail || 'Failed to initialize Twitter login', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('Failed to connect to Twitter', 'error')
        }
    }

    const handleConnectSmartThings = async () => {
        try {
            const res = await fetch('/api/connection/smartthings/auth-url', {
                headers: getAuthHeaders()
            })
            if (res.ok) {
                const data = await res.json()
                if (data.auth_url) {
                    window.location.href = data.auth_url
                }
            } else {
                const err = await res.json()
                showStatus(err.detail || 'Failed to initialize SmartThings login', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('Failed to connect to SmartThings', 'error')
        }
    }

    const handleConnectYouTube = async () => {
        try {
            const res = await fetch('/api/connection/youtube/auth-url', {
                headers: getAuthHeaders()
            })
            if (res.ok) {
                const data = await res.json()
                if (data.auth_url) {
                    window.location.href = data.auth_url
                }
            } else {
                const err = await res.json()
                showStatus(err.detail || 'Failed to initialize YouTube login', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('Failed to connect to YouTube', 'error')
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

    const handleRemoveInstagram = async () => {
        if (!confirm('Are you sure you want to remove the Instagram connection?')) return
        try {
            const res = await fetch('/api/connection/instagram/remove', {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                showStatus('Instagram connection removed', 'success')
                fetchVault()
            } else {
                showStatus('Failed to remove Instagram connection', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('An error occurred during removal', 'error')
        }
    }

    const handleRemoveTwitter = async () => {
        if (!confirm('Are you sure you want to remove the Twitter connection?')) return
        try {
            const res = await fetch('/api/connection/twitter/remove', {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                showStatus('Twitter connection removed', 'success')
                fetchVault()
            } else {
                showStatus('Failed to remove Twitter connection', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('An error occurred during removal', 'error')
        }
    }

    const handleRemoveSmartThings = async () => {
        if (!confirm('Are you sure you want to remove the SmartThings connection?')) return
        try {
            const res = await fetch('/api/connection/smartthings/remove', {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                showStatus('SmartThings connection removed', 'success')
                fetchVault()
            } else {
                showStatus('Failed to remove SmartThings connection', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('An error occurred during removal', 'error')
        }
    }

    const handleRemoveYouTube = async () => {
        if (!confirm('Are you sure you want to remove the YouTube connection?')) return
        try {
            const res = await fetch('/api/connection/youtube/remove', {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                showStatus('YouTube connection removed', 'success')
                fetchVault()
            } else {
                showStatus('Failed to remove YouTube connection', 'error')
            }
        } catch (err) {
            console.error(err)
            showStatus('An error occurred during removal', 'error')
        }
    }

    const isGoogleConnected = vault.some(v => v.key === 'GOOGLE_OAUTH_REFRESH_TOKEN')
    const isInstagramConnected = vault.some(v => v.key === 'INSTAGRAM_OAUTH_TOKEN')
    const isTwitterConnected = vault.some(v => v.key === 'TWITTER_OAUTH_TOKEN' || v.key === 'TWITTER_REFRESH_TOKEN')
    const isSmartThingsConnected = vault.some(v => v.key === 'SMARTTHINGS_OAUTH_TOKEN')
    const isYouTubeConnected = vault.some(v => v.key === 'YOUTUBE_OAUTH_TOKEN' || v.key === 'YOUTUBE_REFRESH_TOKEN')

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
                        {/* Google / GMail */}
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

                        {/* YouTube */}
                        <div className="vault-item">
                            <div className="vault-info">
                                <span className="vault-key" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem' }}>
                                    <i className="fa fa-youtube-play" style={{ color: '#FF0000', fontSize: '1.3rem' }}></i> YouTube
                                </span>
                                <span className="vault-value">
                                    <span className={`status-badge ${isYouTubeConnected ? 'on' : 'off'}`}>
                                        {isYouTubeConnected ? 'Connected' : 'Not Connected'}
                                    </span>
                                </span>
                            </div>
                            <div className="vault-actions">
                                {isYouTubeConnected ? (
                                    <button className="delete-button" onClick={handleRemoveYouTube} title="Remove Connection">
                                        <i className="fa fa-unlink"></i> Disconnect
                                    </button>
                                ) : (
                                    <button className="edit-button" style={{ backgroundColor: '#FF0000', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleConnectYouTube} title="Connect">
                                        <i className="fa fa-link"></i> Connect
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Instagram */}
                        <div className="vault-item">
                            <div className="vault-info">
                                <span className="vault-key" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem' }}>
                                    <i className="fa fa-instagram" style={{ color: '#E1306C', fontSize: '1.3rem' }}></i> Instagram
                                </span>
                                <span className="vault-value">
                                    <span className={`status-badge ${isInstagramConnected ? 'on' : 'off'}`}>
                                        {isInstagramConnected ? 'Connected' : 'Not Connected'}
                                    </span>
                                </span>
                            </div>
                            <div className="vault-actions">
                                {isInstagramConnected ? (
                                    <button className="delete-button" onClick={handleRemoveInstagram} title="Remove Connection">
                                        <i className="fa fa-unlink"></i> Disconnect
                                    </button>
                                ) : (
                                    <button className="edit-button" style={{ backgroundColor: '#E1306C', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleConnectInstagram} title="Connect">
                                        <i className="fa fa-link"></i> Connect
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Twitter (X) */}
                        <div className="vault-item">
                            <div className="vault-info">
                                <span className="vault-key" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem' }}>
                                    <i className="fa fa-twitter" style={{ color: '#1DA1F2', fontSize: '1.3rem' }}></i> X (Twitter)
                                </span>
                                <span className="vault-value">
                                    <span className={`status-badge ${isTwitterConnected ? 'on' : 'off'}`}>
                                        {isTwitterConnected ? 'Connected' : 'Not Connected'}
                                    </span>
                                </span>
                            </div>
                            <div className="vault-actions">
                                {isTwitterConnected ? (
                                    <button className="delete-button" onClick={handleRemoveTwitter} title="Remove Connection">
                                        <i className="fa fa-unlink"></i> Disconnect
                                    </button>
                                ) : (
                                    <button className="edit-button" style={{ backgroundColor: '#1DA1F2', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleConnectTwitter} title="Connect">
                                        <i className="fa fa-link"></i> Connect
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* SmartThings */}
                        <div className="vault-item">
                            <div className="vault-info">
                                <span className="vault-key" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '1.1rem' }}>
                                    <i className="fa fa-home" style={{ color: '#00a3ff', fontSize: '1.3rem' }}></i> SmartThings
                                </span>
                                <span className="vault-value">
                                    <span className={`status-badge ${isSmartThingsConnected ? 'on' : 'off'}`}>
                                        {isSmartThingsConnected ? 'Connected' : 'Not Connected'}
                                    </span>
                                </span>
                            </div>
                            <div className="vault-actions">
                                {isSmartThingsConnected ? (
                                    <button className="delete-button" onClick={handleRemoveSmartThings} title="Remove Connection">
                                        <i className="fa fa-unlink"></i> Disconnect
                                    </button>
                                ) : (
                                    <button className="edit-button" style={{ backgroundColor: '#00a3ff', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={handleConnectSmartThings} title="Connect">
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
