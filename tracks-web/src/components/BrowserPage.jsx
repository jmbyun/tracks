import { useState, useEffect } from 'react'
import { getAuthHeaders } from '../auth'
import './BrowserPage.css'

function BrowserPage() {
    const [currentPath, setCurrentPath] = useState('')
    const [items, setItems] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    // Preview state
    const [previewFile, setPreviewFile] = useState(null) // { name, path, content, isImage }
    const [previewLoading, setPreviewLoading] = useState(false)


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

    const handleItemClick = async (item) => {
        if (item.isDir) {
            const newPath = currentPath ? `${currentPath}/${item.name}` : item.name
            setCurrentPath(newPath)
        } else {
            // Preview file
            const fullPath = currentPath ? `${currentPath}/${item.name}` : item.name
            const fileUrl = `/api/browser/file?path=${encodeURIComponent(fullPath)}`

            const ext = item.name.split('.').pop().toLowerCase()
            const imageExts = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']
            const isImage = imageExts.includes(ext)

            setPreviewFile({ name: item.name, path: fullPath, isImage, content: null })
            setPreviewLoading(true)

            try {
                if (isImage) {
                    // For images, we fetch as blob to create an object URL since it needs auth headers
                    const res = await fetch(fileUrl, { headers: getAuthHeaders() })
                    if (!res.ok) throw new Error('Failed to load image')
                    const blob = await res.blob()
                    const objectUrl = URL.createObjectURL(blob)
                    setPreviewFile({ name: item.name, path: fullPath, isImage: true, content: objectUrl })
                } else {
                    // Try to fetch as text
                    const res = await fetch(fileUrl, { headers: getAuthHeaders() })
                    if (!res.ok) throw new Error('Failed to load file content')

                    // Check if it's too large (e.g., > 1MB)
                    const size = parseInt(res.headers.get('content-length') || '0', 10)
                    if (size > 1024 * 1024) {
                        setPreviewFile({ name: item.name, path: fullPath, isImage: false, content: 'File is too large to preview directly. Please download.' })
                    } else {
                        const text = await res.text()
                        setPreviewFile({ name: item.name, path: fullPath, isImage: false, content: text })
                    }
                }
            } catch (err) {
                console.error('Preview error:', err)
                setPreviewFile({ name: item.name, path: fullPath, isImage: false, content: `Error previewing file: ${err.message}` })
            } finally {
                setPreviewLoading(false)
            }
        }
    }

    const closePreview = () => {
        if (previewFile && previewFile.isImage && previewFile.content) {
            URL.revokeObjectURL(previewFile.content)
        }
        setPreviewFile(null)
    }

    const handleDownload = (e, item) => {
        e.stopPropagation()
        const fullPath = currentPath ? `${currentPath}/${item.name}` : item.name
        const downloadUrl = item.isDir
            ? `/api/browser/download-dir?path=${encodeURIComponent(fullPath)}`
            : `/api/browser/file?path=${encodeURIComponent(fullPath)}`
        downloadFile(downloadUrl, item.isDir ? `${item.name}.zip` : item.name)
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
                                    <th className="action-column">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentPath && (
                                    <tr className="file-row up-dir" onClick={navigateUp}>
                                        <td colSpan="4">
                                            <div className="file-name-cell">
                                                <i className="fa fa-level-up"></i>
                                                <span>..</span>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {items.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="empty-dir">This folder is empty</td>
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
                                            <td className="action-column">
                                                <button
                                                    className="download-icon-btn"
                                                    onClick={(e) => handleDownload(e, item)}
                                                    title="Download"
                                                >
                                                    <i className="fa fa-download"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    )}
                </div>

                {previewFile && (
                    <div className="file-preview-overlay" onClick={closePreview}>
                        <div className="file-preview-modal" onClick={e => e.stopPropagation()}>
                            <div className="preview-header">
                                <h3>{previewFile.name}</h3>
                                <div className="preview-actions">
                                    <button
                                        className="preview-download-btn"
                                        onClick={(e) => {
                                            const downloadUrl = `/api/browser/file?path=${encodeURIComponent(previewFile.path)}`
                                            downloadFile(downloadUrl, previewFile.name)
                                        }}
                                    >
                                        <i className="fa fa-download"></i> Download
                                    </button>
                                    <button className="preview-close-btn" onClick={closePreview}>
                                        <i className="fa fa-times"></i>
                                    </button>
                                </div>
                            </div>
                            <div className="preview-body">
                                {previewLoading ? (
                                    <div className="preview-loading">Loading preview...</div>
                                ) : previewFile.isImage ? (
                                    <div className="image-preview-container">
                                        <img src={previewFile.content} alt={previewFile.name} />
                                    </div>
                                ) : (
                                    <pre className="text-preview-container">
                                        <code>{previewFile.content}</code>
                                    </pre>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default BrowserPage
