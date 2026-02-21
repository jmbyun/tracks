import { useState, useEffect } from 'react'
import { getAuthHeaders } from '../auth'
import './SettingsPage.css'

const CONFIG_KEYS = [
    { key: 'HEARTBEAT_COOLDOWN_SECONDS', label: 'Heartbeat Cooldown (s)', type: 'number' },
    { key: 'ON_DEMAND_COOLDOWN_SECONDS', label: 'On-Demand Cooldown (s)', type: 'number' },
    { key: 'ENABLE_TELEGRAM', label: 'Enable Telegram', type: 'boolean' },
    { key: 'AGENT_USE_ORDER', label: 'Agent Use Order', type: 'text', placeholder: 'e.g., codex,gemini' }
]

const VAULT_KEY_OPTIONS = [
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_USER_IDS',
    'Custom'
]

function SettingsPage() {
    const [config, setConfig] = useState({})
    const [vault, setVault] = useState([])
    const [defaults, setDefaults] = useState({})
    const [activeClient, setActiveClient] = useState('')
    const [availableClients, setAvailableClients] = useState([])
    const [isLoading, setIsLoading] = useState(true)

    const [isSaving, setIsSaving] = useState(false)
    const [message, setMessage] = useState({ text: '', type: '' })
    const [visibleVaultItems, setVisibleVaultItems] = useState({})
    const [editingVaultItem, setEditingVaultItem] = useState(null) // { key, value }



    // Vault form state
    const [newVaultItem, setNewVaultItem] = useState({ key: '', selectedKey: 'TELEGRAM_BOT_TOKEN', value: '' })
    const [editingVaultKey, setEditingVaultKey] = useState(null)

    useEffect(() => {
        fetchSettings()
    }, [])

    const fetchSettings = async () => {
        setIsLoading(true)
        try {
            // Fetch individually to be more resilient
            const fetchConfig = async () => {
                try {
                    const res = await fetch('/api/settings/config', { headers: getAuthHeaders() })
                    if (res.ok) setConfig(await res.json())
                } catch (e) { console.error('Config fetch failed:', e) }
            }

            const fetchVault = async () => {
                try {
                    const res = await fetch('/api/settings/vault', { headers: getAuthHeaders() })
                    if (res.ok) setVault(await res.json())
                } catch (e) { console.error('Vault fetch failed:', e) }
            }

            const fetchDefaults = async () => {
                try {
                    const res = await fetch('/api/settings/defaults', { headers: getAuthHeaders() })
                    if (res.ok) setDefaults(await res.json())
                } catch (e) { console.error('Defaults fetch failed:', e) }
            }

            const fetchActiveClient = async () => {
                try {
                    const res = await fetch('/api/settings/active-client', { headers: getAuthHeaders() })
                    if (res.ok) {
                        const data = await res.json()
                        setActiveClient(data.active_client)
                        setAvailableClients(data.available_clients)
                    }
                } catch (e) { console.error('Active client fetch failed:', e) }
            }

            await Promise.all([fetchConfig(), fetchVault(), fetchDefaults(), fetchActiveClient()])
        } catch (error) {
            console.error('Error fetching settings:', error)
            showStatus('Failed to load settings', 'error')
        } finally {
            setIsLoading(false)
        }
    }


    const showStatus = (text, type) => {
        setMessage({ text, type })
        setTimeout(() => setMessage({ text: '', type: '' }), 3000)
    }

    const handleConfigChange = (key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }

    const handleActiveClientChange = async (e) => {
        const newClient = e.target.value
        setActiveClient(newClient)
        setIsSaving(true)
        try {
            const res = await fetch('/api/settings/active-client', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ client_type: newClient })
            })
            if (res.ok) {
                showStatus('Active client updated', 'success')
            } else {
                showStatus('Failed to update active client', 'error')
            }
        } catch (error) {
            showStatus('Error updating active client', 'error')
        } finally {
            setIsSaving(false)
        }
    }



    const saveConfig = async () => {
        setIsSaving(true)
        try {
            const res = await fetch('/api/settings/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify(config)
            })
            if (res.ok) {
                showStatus('Configuration saved', 'success')
            } else {
                showStatus('Failed to save configuration', 'error')
            }
        } catch (error) {
            showStatus('Error saving configuration', 'error')
        } finally {
            setIsSaving(false)
        }
    }

    const handleAddVaultItem = async (e) => {
        e.preventDefault()
        const key = newVaultItem.selectedKey === 'Custom' ? newVaultItem.key : newVaultItem.selectedKey
        if (!key || !newVaultItem.value) return

        setIsSaving(true)
        try {
            const res = await fetch('/api/settings/vault', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ key, value: newVaultItem.value })
            })
            if (res.ok) {
                setNewVaultItem({ key: '', selectedKey: 'TELEGRAM_BOT_TOKEN', value: '' })
                fetchSettings()
                showStatus('Vault item added', 'success')
            } else {
                const data = await res.json()
                showStatus(data.detail || 'Failed to add vault item', 'error')
            }
        } catch (error) {
            showStatus('Error adding vault item', 'error')
        } finally {
            setIsSaving(false)
        }
    }

    const handleDeleteVaultItem = async (key) => {
        if (!confirm(`Delete ${key}?`)) return
        try {
            const res = await fetch(`/api/settings/vault/${key}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            })
            if (res.ok) {
                fetchSettings()
                showStatus('Vault item deleted', 'success')
            }
        } catch (error) {
            showStatus('Error deleting vault item', 'error')
        }
    }

    const handleUpdateVaultItem = async (oldKey) => {
        if (!editingVaultItem.key || !editingVaultItem.value) return
        setIsSaving(true)
        try {
            const res = await fetch(`/api/settings/vault/${oldKey}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ key: editingVaultItem.key, value: editingVaultItem.value })
            })
            if (res.ok) {
                setEditingVaultItem(null)
                fetchSettings()
                showStatus('Vault item updated', 'success')
            } else {
                const data = await res.json()
                showStatus(data.detail || 'Failed to update vault item', 'error')
            }
        } catch (error) {
            showStatus('Error updating vault item', 'error')
        } finally {
            setIsSaving(false)
        }
    }

    const startEditing = (item) => {
        setEditingVaultItem({ ...item })
        setVisibleVaultItems(prev => ({ ...prev, [item.key]: true }))
    }

    const toggleVaultVisibility = (key) => {

        setVisibleVaultItems(prev => ({ ...prev, [key]: !prev[key] }))
    }

    if (isLoading) {

        return <div className="settings-loading">Loading settings...</div>
    }

    return (
        <div className="settings-page">
            <div className="settings-container">
                <header className="settings-header">
                    <h1>Settings</h1>
                    {message.text && (
                        <div className={`status-message ${message.type}`}>
                            {message.text}
                        </div>
                    )}
                </header>

                <section className="settings-section active-client-section">
                    <h2>Active LLM Client</h2>
                    <div className="config-grid">
                        <div className="config-item">
                            <div className="config-label-group">
                                <label>Currently Selected Client</label>
                                <span className="default-hint">Select the active LLM agent for execution tasks</span>
                            </div>
                            <select
                                value={activeClient}
                                onChange={handleActiveClientChange}
                                className="active-client-select"
                                disabled={isSaving}
                            >
                                {availableClients.map(client => (
                                    <option key={client} value={client}>{client}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </section>

                <section className="settings-section">
                    <h2>Application Configuration</h2>
                    <div className="config-grid">
                        {CONFIG_KEYS.map(item => (
                            <div key={item.key} className="config-item">
                                <div className="config-label-group">
                                    <label>{item.label}</label>
                                    <span className="default-hint">Default: {String(defaults[item.key] ?? '')}</span>
                                </div>
                                {item.type === 'boolean' ? (
                                    <div className="toggle-switch">
                                        <input
                                            type="checkbox"
                                            checked={config[item.key] ?? defaults[item.key] ?? false}
                                            onChange={(e) => handleConfigChange(item.key, e.target.checked)}
                                        />
                                        <span className="slider"></span>
                                    </div>
                                ) : (
                                    <input
                                        type={item.type}
                                        value={config[item.key] ?? defaults[item.key] ?? ''}
                                        placeholder={String(defaults[item.key] ?? '')}
                                        onChange={(e) => handleConfigChange(item.key, item.type === 'number' ? parseInt(e.target.value) : e.target.value)}
                                    />
                                )}
                            </div>

                        ))}
                    </div>
                    <button className="save-button" onClick={saveConfig} disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save Configuration'}
                    </button>
                </section>

                <section className="settings-section">
                    <h2>Vault (Secrets)</h2>
                    <div className="vault-list">
                        {vault.map(item => (
                            <div key={item.key} className={`vault-item ${editingVaultItem?.key === item.key ? 'editing' : ''}`}>
                                {editingVaultItem?.key === item.key ? (
                                    <div className="vault-edit-row">
                                        <input
                                            type="text"
                                            value={editingVaultItem.key}
                                            onChange={(e) => setEditingVaultItem(prev => ({ ...prev, key: e.target.value }))}
                                            placeholder="Key"
                                        />
                                        <input
                                            type="text"
                                            value={editingVaultItem.value}
                                            onChange={(e) => setEditingVaultItem(prev => ({ ...prev, value: e.target.value }))}
                                            placeholder="Value"
                                        />
                                        <div className="vault-actions">
                                            <button className="save-icon-button" onClick={() => handleUpdateVaultItem(item.key)} title="Save">
                                                <i className="fa fa-check"></i>
                                            </button>
                                            <button className="cancel-icon-button" onClick={() => setEditingVaultItem(null)} title="Cancel">
                                                <i className="fa fa-times"></i>
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="vault-info">
                                            <span className="vault-key">{item.key}</span>
                                            <span className="vault-value">
                                                {visibleVaultItems[item.key] ? item.value : '••••••••'}
                                            </span>
                                        </div>
                                        <div className="vault-actions">
                                            <button
                                                className="reveal-button"
                                                onClick={() => toggleVaultVisibility(item.key)}
                                                title={visibleVaultItems[item.key] ? "Hide" : "Reveal"}
                                            >
                                                <i className={`fa fa-${visibleVaultItems[item.key] ? 'eye-slash' : 'eye'}`}></i>
                                            </button>
                                            <button className="edit-button" onClick={() => startEditing(item)} title="Edit">
                                                <i className="fa fa-pencil"></i>
                                            </button>
                                            <button className="delete-button" onClick={() => handleDeleteVaultItem(item.key)} title="Delete">
                                                <i className="fa fa-trash"></i>
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}

                    </div>


                    <form className="add-vault-form" onSubmit={handleAddVaultItem}>
                        <h3>Add New Secret</h3>
                        <div className="form-row">
                            <select
                                value={newVaultItem.selectedKey}
                                onChange={(e) => setNewVaultItem(prev => ({ ...prev, selectedKey: e.target.value }))}
                            >
                                {VAULT_KEY_OPTIONS.map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                            {newVaultItem.selectedKey === 'Custom' && (
                                <input
                                    type="text"
                                    placeholder="Enter custom key"
                                    value={newVaultItem.key}
                                    onChange={(e) => setNewVaultItem(prev => ({ ...prev, key: e.target.value }))}
                                    required
                                />
                            )}
                            <input
                                type="password"
                                placeholder="Value"
                                value={newVaultItem.value}
                                onChange={(e) => setNewVaultItem(prev => ({ ...prev, value: e.target.value }))}
                                required
                            />
                            <button type="submit" className="add-button" disabled={isSaving}>
                                Add
                            </button>
                        </div>
                    </form>
                </section>
            </div>
        </div>
    )
}

export default SettingsPage
