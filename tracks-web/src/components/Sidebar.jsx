import { useState, useEffect, useRef } from 'react'
import './Sidebar.css'
import HistoryItem from './HistoryItem'

function Sidebar({
    isOpen,
    onClose,
    onNewChat,
    conversations,
    heartbeatSessions,
    onLoadConversation,
    onLoadHeartbeatSession,
    activeSessionId,
    onLoadMore,
    onLoadMoreHeartbeat,
    hasMore,
    hasMoreHeartbeat,
    telegramSessions,
    onLoadTelegramSession,
    onLoadMoreTelegram,
    hasMoreTelegram,
    onLogout
}) {
    const historyListRef = useRef(null)
    const [activeTab, setActiveTab] = useState('chats') // 'chats', 'heartbeat', or 'telegram'

    // Handle scroll to detect bottom
    const handleScroll = () => {
        if (!historyListRef.current) return

        const { scrollTop, scrollHeight, clientHeight } = historyListRef.current
        // Load more when scrolled to bottom (with 50px threshold)
        if (scrollHeight - scrollTop - clientHeight < 50) {
            if (activeTab === 'chats' && hasMore) {
                onLoadMore()
            } else if (activeTab === 'heartbeat' && hasMoreHeartbeat) {
                onLoadMoreHeartbeat()
            } else if (activeTab === 'telegram' && hasMoreTelegram) {
                onLoadMoreTelegram()
            }
        }
    }

    // Format timestamp to "yyyy-mm-dd hh:MM"
    const formatHeartbeatTime = (timestamp) => {
        try {
            const date = new Date(timestamp)
            if (isNaN(date.getTime())) return 'Invalid Date'

            const year = date.getFullYear()
            const month = String(date.getMonth() + 1).padStart(2, '0')
            const day = String(date.getDate()).padStart(2, '0')
            const hours = String(date.getHours()).padStart(2, '0')
            const mins = String(date.getMinutes()).padStart(2, '0')

            return `${year}-${month}-${day} ${hours}:${mins}`
        } catch {
            return ''
        }
    }

    const currentList = activeTab === 'chats' ? conversations : (activeTab === 'heartbeat' ? heartbeatSessions : telegramSessions)
    const currentHasMore = activeTab === 'chats' ? hasMore : (activeTab === 'heartbeat' ? hasMoreHeartbeat : hasMoreTelegram)
    const currentLoadMore = activeTab === 'chats' ? onLoadMore : (activeTab === 'heartbeat' ? onLoadMoreHeartbeat : onLoadMoreTelegram)

    return (
        <>
            {/* Mobile overlay */}
            {isOpen && <div className="sidebar-overlay" onClick={onClose}></div>}

            <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
                <div className="sidebar-header">
                    <button className="sidebar-close" onClick={onClose}>
                        <i className="fa fa-times"></i>
                    </button>
                </div>

                <div className="sidebar-content">
                    {/* New Chat Button */}
                    <button className="new-chat-button" onClick={onNewChat}>
                        <i className="fa fa-edit"></i>
                        <span>New chat</span>
                    </button>

                    {/* Tab Switcher */}
                    <div className="tab-switcher">
                        <button
                            className={`tab-button ${activeTab === 'chats' ? 'active' : ''}`}
                            onClick={() => setActiveTab('chats')}
                        >
                            Chats
                        </button>
                        <button
                            className={`tab-button ${activeTab === 'heartbeat' ? 'active' : ''}`}
                            onClick={() => setActiveTab('heartbeat')}
                        >
                            Heartbeat
                        </button>
                        <button
                            className={`tab-button ${activeTab === 'telegram' ? 'active' : ''}`}
                            onClick={() => setActiveTab('telegram')}
                        >
                            Telegram
                        </button>
                    </div>

                    {/* History Section */}
                    {currentList.length > 0 && (
                        <div className="history-section">
                            <div
                                className="history-list"
                                ref={historyListRef}
                                onScroll={handleScroll}
                            >
                                {activeTab === 'chats' ? (
                                    conversations.map((conv) => (
                                        <HistoryItem
                                            key={conv.session_id + conv.timestamp}
                                            conversation={conv}
                                            isActive={conv.session_id === activeSessionId}
                                            onClick={() => onLoadConversation(conv.session_id)}
                                        />
                                    ))
                                ) : activeTab === 'telegram' ? (
                                    telegramSessions.map((conv) => (
                                        <HistoryItem
                                            key={conv.session_id + conv.timestamp}
                                            conversation={conv}
                                            isActive={conv.session_id === activeSessionId}
                                            onClick={() => onLoadTelegramSession(conv.session_id)}
                                        />
                                    ))
                                ) : (
                                    heartbeatSessions.map((session) => (
                                        <div
                                            key={session.session_id + session.timestamp}
                                            className={`history-item ${session.session_id === activeSessionId ? 'active' : ''}`}
                                            onClick={() => onLoadHeartbeatSession(session.session_id)}
                                        >
                                            <div className="history-item-content">
                                                <div className="history-item-message heartbeat-time">
                                                    {formatHeartbeatTime(session.timestamp)}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>

                            {currentHasMore && (
                                <button className="load-more-button" onClick={currentLoadMore}>
                                    Load more
                                </button>
                            )}
                        </div>
                    )}

                    {currentList.length === 0 && (
                        <div className="empty-list">
                            No {activeTab === 'chats' ? 'conversations' : (activeTab === 'telegram' ? 'telegram sessions' : 'heartbeat sessions')} yet
                        </div>
                    )}

                    {onLogout && (
                        <div className="sidebar-footer">
                            <button className="logout-button" onClick={onLogout}>
                                <i className="fa fa-sign-out"></i>
                                <span>Log out</span>
                            </button>
                        </div>
                    )}
                </div>
            </aside>
        </>
    )
}

export default Sidebar

