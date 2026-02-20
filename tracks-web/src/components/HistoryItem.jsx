import './HistoryItem.css'

function HistoryItem({ conversation, isActive, onClick }) {
    // Format timestamp to relative time
    const getRelativeTime = (timestamp) => {
        try {
            const date = new Date(timestamp)

            // Check if date is valid
            if (isNaN(date.getTime())) {
                console.error('Invalid timestamp:', timestamp)
                return 'Invalid Date'
            }

            const now = new Date()
            const diffMs = now - date
            const diffMins = Math.floor(diffMs / 60000)
            const diffHours = Math.floor(diffMs / 3600000)
            const diffDays = Math.floor(diffMs / 86400000)

            if (diffMins < 1) return 'Just now'
            if (diffMins < 60) return `${diffMins}m ago`
            if (diffHours < 24) return `${diffHours}h ago`
            if (diffDays === 1) return 'Yesterday'
            if (diffDays < 7) return `${diffDays}d ago`

            // Format as date
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        } catch (error) {
            console.error('Error parsing timestamp:', timestamp, error)
            return ''
        }
    }

    return (
        <div
            className={`history-item ${isActive ? 'active' : ''}`}
            onClick={onClick}
        >
            <div className="history-item-content">
                <div className="history-item-message">{conversation.first_message}</div>
                <div className="history-item-time">{getRelativeTime(conversation.timestamp)}</div>
            </div>
        </div>
    )
}

export default HistoryItem
