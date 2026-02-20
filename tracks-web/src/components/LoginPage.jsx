import { useState } from 'react'
import { setApiKey, validateApiKey } from '../auth'
import './LoginPage.css'

function LoginPage({ onLogin }) {
    const [key, setKey] = useState('')
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!key.trim() || isLoading) return

        setIsLoading(true)
        setError('')

        const valid = await validateApiKey(key.trim())

        if (valid) {
            setApiKey(key.trim())
            onLogin()
        } else {
            setError('Invalid API Key. Please try again.')
        }

        setIsLoading(false)
    }

    return (
        <div className="login-page">
            <div className="login-card">
                <h1>Tracks</h1>
                <p>Enter your API Key to continue.</p>
                <form className="login-form" onSubmit={handleSubmit}>
                    <input
                        className="login-input"
                        type="password"
                        placeholder="API Key"
                        value={key}
                        onChange={(e) => setKey(e.target.value)}
                        autoFocus
                    />
                    {error && <p className="login-error">{error}</p>}
                    <button
                        className="login-button"
                        type="submit"
                        disabled={!key.trim() || isLoading}
                    >
                        {isLoading ? 'Validating…' : 'Log In'}
                    </button>
                </form>
            </div>
        </div>
    )
}

export default LoginPage
