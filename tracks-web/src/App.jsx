import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import LoginPage from './components/LoginPage'
import SettingsPage from './components/SettingsPage'
import BrowserPage from './components/BrowserPage'
import { getApiKey, getAuthHeaders, clearApiKey, validateApiKey } from './auth'


import './App.css'

function ChatPage({ onLogout, showSettings, showBrowser }) {

  const navigate = useNavigate()

  const { sessionId: urlSessionId } = useParams()

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sessionId, setSessionId] = useState(urlSessionId === 'new' ? null : urlSessionId)
  const [messages, setMessages] = useState([])
  const [isScrolled, setIsScrolled] = useState(false)
  const [utcOffset, setUtcOffset] = useState(null)

  // History state
  const [conversations, setConversations] = useState([])
  const [hasMoreHistory, setHasMoreHistory] = useState(false)
  const [historyOffset, setHistoryOffset] = useState(0)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  // Heartbeat sessions state
  const [heartbeatSessions, setHeartbeatSessions] = useState([])
  const [hasMoreHeartbeat, setHasMoreHeartbeat] = useState(false)
  const [heartbeatOffset, setHeartbeatOffset] = useState(0)
  const [isLoadingHeartbeat, setIsLoadingHeartbeat] = useState(false)

  // Telegram sessions state
  const [telegramSessions, setTelegramSessions] = useState([])
  const [hasMoreTelegram, setHasMoreTelegram] = useState(false)
  const [telegramOffset, setTelegramOffset] = useState(0)
  const [isLoadingTelegram, setIsLoadingTelegram] = useState(false)

  // Load initial history on mount
  useEffect(() => {
    loadHistory(0)
    loadHeartbeatHistory(0)
    loadTelegramHistory(0)
    fetchConfig()

    const handleWindowScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }

    window.addEventListener('scroll', handleWindowScroll)
    return () => window.removeEventListener('scroll', handleWindowScroll)
  }, [])

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/settings/config', {
        headers: { ...getAuthHeaders() }
      })
      if (response.ok) {
        const data = await response.json()
        if (data.UTC_OFFSET !== undefined) {
          setUtcOffset(data.UTC_OFFSET)
        }
      }
    } catch (error) {
      console.error('Error fetching config:', error)
    }
  }

  // Track if we should skip the next URL-based load (e.g., during active streaming)
  const skipNextLoadRef = useRef(false)

  // Load conversation when URL changes
  useEffect(() => {
    const loadConversationFromUrl = async () => {
      // Skip if we just navigated from an active session
      if (skipNextLoadRef.current) {
        skipNextLoadRef.current = false
        return
      }

      if (urlSessionId && urlSessionId !== 'new') {
        try {
          // Try regular history first
          let response = await fetch(`/api/history/${urlSessionId}`, {
            headers: { ...getAuthHeaders() }
          })

          // If not found, try heartbeat history
          if (!response.ok) {
            response = await fetch(`/api/heartbeat/history/${urlSessionId}`, {
              headers: { ...getAuthHeaders() }
            })
          }

          if (response.ok) {
            const data = await response.json()

            // Set messages from history
            setMessages(data.messages.map(msg => ({
              role: msg.role,
              content: msg.content,
              serialized_output: msg.serialized_output,
              timestamp: msg.timestamp
            })))

            // Set session ID
            setSessionId(urlSessionId)
          } else {
            console.error('Session not found:', urlSessionId)
          }
        } catch (error) {
          console.error('Error loading conversation:', error)
        }
      } else {
        // New chat or root path
        setSessionId(null)
        setMessages([])
      }
    }

    loadConversationFromUrl()
  }, [urlSessionId])

  // Load history from API
  const loadHistory = async (offset) => {
    if (isLoadingHistory) return

    setIsLoadingHistory(true)
    try {
      const response = await fetch(`/api/history?limit=30&offset=${offset}`, {
        headers: { ...getAuthHeaders() }
      })
      const data = await response.json()

      if (offset === 0) {
        setConversations(data.conversations)
      } else {
        setConversations(prev => [...prev, ...data.conversations])
      }

      setHasMoreHistory(data.has_more)
      setHistoryOffset(offset + data.conversations.length)
    } catch (error) {
      console.error('Error loading history:', error)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const handleLoadMore = () => {
    loadHistory(historyOffset)
  }

  // Load heartbeat history from API
  const loadHeartbeatHistory = async (offset) => {
    if (isLoadingHeartbeat) return

    setIsLoadingHeartbeat(true)
    try {
      const response = await fetch(`/api/heartbeat/history?limit=30&offset=${offset}`, {
        headers: { ...getAuthHeaders() }
      })
      const data = await response.json()

      if (offset === 0) {
        setHeartbeatSessions(data.conversations || [])
      } else {
        setHeartbeatSessions(prev => [...prev, ...(data.conversations || [])])
      }

      setHasMoreHeartbeat(data.has_more || false)
      setHeartbeatOffset(offset + (data.conversations?.length || 0))
    } catch (error) {
      console.error('Error loading heartbeat history:', error)
    } finally {
      setIsLoadingHeartbeat(false)
    }
  }

  const handleLoadMoreHeartbeat = () => {
    loadHeartbeatHistory(heartbeatOffset)
  }

  // Load telegram history from API
  const loadTelegramHistory = async (offset) => {
    if (isLoadingTelegram) return

    setIsLoadingTelegram(true)
    try {
      const response = await fetch(`/api/telegram/history?limit=30&offset=${offset}`, {
        headers: { ...getAuthHeaders() }
      })
      const data = await response.json()

      if (offset === 0) {
        setTelegramSessions(data.conversations || [])
      } else {
        setTelegramSessions(prev => [...prev, ...(data.conversations || [])])
      }

      setHasMoreTelegram(data.has_more || false)
      setTelegramOffset(offset + (data.conversations?.length || 0))
    } catch (error) {
      console.error('Error loading telegram history:', error)
    } finally {
      setIsLoadingTelegram(false)
    }
  }

  const handleLoadMoreTelegram = () => {
    loadTelegramHistory(telegramOffset)
  }

  const handleLoadHeartbeatSession = async (loadSessionId) => {
    // Navigate to heartbeat session view
    // For now, just navigate to sessions - could add a separate route
    navigate(`/sessions/${loadSessionId}`)
    setSidebarOpen(false)
  }

  const handleLoadConversation = async (loadSessionId) => {
    // Just navigate - the useEffect will handle loading
    navigate(`/sessions/${loadSessionId}`)
    setSidebarOpen(false)
  }

  const handleLoadTelegramSession = async (loadSessionId) => {
    navigate(`/sessions/${loadSessionId}`)
    setSidebarOpen(false)
  }

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const handleNewChat = () => {
    navigate('/sessions/new')
    setSidebarOpen(false)
  }

  const handleSendMessage = (message) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: message, timestamp: new Date().toISOString() }])
  }

  const handleStreamMessage = (contentOrData, tag) => {
    // Update or add assistant message
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1]

      if (lastMessage && lastMessage.role === 'assistant') {
        // Append to existing assistant message
        const newSerializedOutput = [...(lastMessage.serialized_output || [])]

        if (tag) {
          newSerializedOutput.push({ tag, data: contentOrData })
        }

        let newContent = lastMessage.content
        if (tag === 'agent' || !tag) {
          newContent += contentOrData
        }

        return [
          ...prev.slice(0, -1),
          {
            ...lastMessage,
            content: newContent,
            serialized_output: newSerializedOutput
          }
        ]
      } else {
        // Create new assistant message
        return [...prev, {
          role: 'assistant',
          content: (tag === 'agent' || !tag) ? contentOrData : '',
          serialized_output: tag ? [{ tag, data: contentOrData }] : []
        }]
      }
    })
  }

  const handleSessionUpdate = (newSessionId) => {
    setSessionId(newSessionId)
    // Skip the URL-based load since we're already streaming
    skipNextLoadRef.current = true
    // Update URL to new session
    navigate(`/sessions/${newSessionId}`)
    // Reload history to show new conversation
    loadHistory(0)
  }

  return (
    <div className="app">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        conversations={conversations}
        heartbeatSessions={heartbeatSessions}
        onLoadConversation={handleLoadConversation}
        onLoadHeartbeatSession={handleLoadHeartbeatSession}
        activeSessionId={sessionId}
        onLoadMore={handleLoadMore}
        onLoadMoreHeartbeat={handleLoadMoreHeartbeat}
        hasMore={hasMoreHistory}
        hasMoreHeartbeat={hasMoreHeartbeat}
        telegramSessions={telegramSessions}
        onLoadTelegramSession={handleLoadTelegramSession}
        onLoadMoreTelegram={handleLoadMoreTelegram}
        hasMoreTelegram={hasMoreTelegram}
        onLogout={onLogout}
      />
      <div className="main-content">
        <header className={`app-header ${isScrolled ? 'scrolled' : ''}`}>
          <button className="menu-button" onClick={toggleSidebar}>
            <i className="fa fa-bars"></i>
          </button>
          <div className="header-left" onClick={handleNewChat} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
            <img src="/icons/icon-mac-128x128.png" alt="Logo" className="app-logo" />
            <h1 className="app-title">Tracks</h1>
          </div>
          <div className="header-right">
            <button className="browser-button" onClick={() => navigate('/browser')} title="Browse Files">
              <i className="fa fa-folder-open"></i>
            </button>
            <button className="settings-button" onClick={() => navigate('/settings')} title="Settings">
              <i className="fa fa-cog"></i>
            </button>
          </div>

        </header>


        {showSettings ? (
          <SettingsPage />
        ) : showBrowser ? (
          <BrowserPage />
        ) : (
          <ChatArea

            messages={messages}
            sessionId={sessionId}
            onSendMessage={handleSendMessage}
            onStreamMessage={handleStreamMessage}
            onSessionUpdate={handleSessionUpdate}
            utcOffset={utcOffset}
          />
        )}

      </div>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const apiKey = getApiKey()
      if (!apiKey) {
        setIsAuthenticated(false)
        setIsCheckingAuth(false)
        return
      }

      const valid = await validateApiKey(apiKey)
      if (!valid) {
        clearApiKey()
        setIsAuthenticated(false)
      } else {
        setIsAuthenticated(true)
      }
      setIsCheckingAuth(false)
    }

    checkAuth()
  }, [])

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    clearApiKey()
    setIsAuthenticated(false)
  }

  if (isCheckingAuth) {
    return null
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <Routes>
      <Route path="/" element={<ChatPage onLogout={handleLogout} />} />
      <Route path="/sessions/:sessionId" element={<ChatPage onLogout={handleLogout} />} />
      <Route path="/settings" element={<ChatPage onLogout={handleLogout} showSettings={true} />} />
      <Route path="/browser" element={<ChatPage onLogout={handleLogout} showBrowser={true} />} />
    </Routes>


  )
}

export default App
