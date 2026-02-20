import { useState, useEffect } from 'react'
import { getAuthHeaders } from '../auth'
import './BrowserPage.css'

function BrowserPage() {
    const [currentPath, setCurrentPath] = useState('')
    const [items, setItems] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchDirectory(currentPath)
    }, [currentPath])

    const fetchDirectory = async (path) => {
        setIsLoading(true)
        setError(null)
        try {
            const res = await fetch(`/api/browser/list?path=${encodeURIComponent(path)}`, {
                headers: getAuthHeaders()
            })
            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Failed to load directory')
            }
            const data = await res.json()
            setItems(data)
        } catch (err) {
            console.error('Browser error:', err)
            setError(err.message)
        } finally {
            setIsLoading(false)
        }
    }

    const handleItemClick = (item) => {
        if (item.isDir) {
            const newPath = currentPath ? `${currentPath}/${item.name}` : item.name
            setCurrentPath(newPath)
        } else {
            // Download file
            const downloadUrl = `/api/browser/file?path=${encodeURIComponent(currentPath ? `${currentPath}/${item.name}` : item.name)}`

            // Standard fetch is needed if API key is required, otherwise simple window.open
            // Since API key is in headers, we need to fetch the blob and download it
            downloadFile(downloadUrl, item.name)
        }
    }

    const downloadFile = async (url, filename) => {
        try {
            const res = await fetch(url, { headers: getAuthHeaders() })
            if (!res.ok) throw new Error('Download failed')
            const blob = await res.blob()
            const link = document.createElement('a')
            link.href = URL.createObjectURL(blob)
            link.download = filename
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        } catch (err) {
            console.error(err)
            setError('Failed to download file')
            setTimeout(() => setError(null), 3000)
        }
    }

    const navigateUp = () => {
        if (!currentPath) return
        const parts = currentPath.split('/')
        parts.pop()
        setCurrentPath(parts.join('/'))
    }

    const navigateToBreadcrumb = (index) => {
        if (index === -1) {
            setCurrentPath('')
            return
        }
        const parts = currentPath.split('/')
        setCurrentPath(parts.slice(0, index + 1).join('/'))
    }

    const formatSize = (bytes) => {
        if (bytes === 0) return '-'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
    }

    const formatDate = (isoString) => {
        const date = new Date(isoString)
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    const pathParts = currentPath ? currentPath.split('/') : []

    return (
        <div className="browser-page">
            <div className="browser-container">
                <header className="browser-header">
                    <div className="breadcrumb">
                        <span
                            className={`crumb ${!currentPath ? 'active' : ''}`}
                            onClick={() => navigateToBreadcrumb(-1)}
                        >
                            <i className="fa fa-home"></i> Home
                        </span>
                        {pathParts.map((part, index) => (
                            <span key={index} className="crumb-part">
                                <span className="separator">/</span>
                                <span
                                    className={`crumb ${index === pathParts.length - 1 ? 'active' : ''}`}
                                    onClick={() => navigateToBreadcrumb(index)}
                                >
                                    {part}
                                </span>
                            </span>
                        ))}
                    </div>
                    {error && <div className="browser-error">{error}</div>}
                </header>

                <div className="browser-content">
                    {isLoading ? (
                        <div className="browser-loading">Loading...</div>
                    ) : (
                        <table className="file-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Last Modified</th>
                                    <th>Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentPath && (
                                    <tr className="file-row up-dir" onClick={navigateUp}>
                                        <td colSpan="3">
                                            <div className="file-name-cell">
                                                <i className="fa fa-level-up"></i>
                                                <span>..</span>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {items.length === 0 ? (
                                    <tr>
                                        <td colSpan="3" className="empty-dir">This folder is empty</td>
                                    </tr>
                                ) : (
                                    items.map(item => (
                                        <tr key={item.id} className="file-row" onClick={() => handleItemClick(item)}>
                                            <td>
                                                <div className="file-name-cell">
                                                    <i className={`fa fa-${item.isDir ? 'folder folder-icon' : 'file-text-o file-icon'}`}></i>
                                                    <span className="file-name">{item.name}</span>
                                                </div>
                                            </td>
                                            <td className="file-date">{formatDate(item.modDate)}</td>
                                            <td className="file-size">{item.isDir ? '-' : formatSize(item.size)}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    )
}

export default BrowserPage
