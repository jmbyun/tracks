import { useState, useRef, useEffect } from 'react'
import { getAuthHeaders } from '../auth'
import './ChatInput.css'

function ChatInput({ sessionId, onSendMessage, onStreamMessage, onSessionUpdate, onLoadingChange }) {
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const textareaRef = useRef(null)

    const adjustTextareaHeight = () => {
        const textarea = textareaRef.current
        if (textarea) {
            textarea.style.height = 'auto'
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
        }
    }

    useEffect(() => {
        adjustTextareaHeight()
    }, [input])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!input.trim() || isLoading) return

        const message = input.trim()
        setInput('')
        setIsLoading(true)
        if (onLoadingChange) onLoadingChange(true)

        // Send user message to parent
        onSendMessage(message)

        try {
            // Make API request with SSE
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    message,
                    session_id: sessionId
                })
            })

            const reader = response.body.getReader()
            const decoder = new TextDecoder()

            let currentEvent = ''
            let hasStartedStreaming = false

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                if (!hasStartedStreaming) {
                    hasStartedStreaming = true
                    // Keep loading indicator during streaming
                    // It will be turned off in the finally block
                }

                const chunk = decoder.decode(value)
                const lines = chunk.split('\n')

                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        currentEvent = line.slice(7).trim()
                    } else if (line.startsWith('data: ')) {
                        const data = line.slice(6)
                        if (data === '[DONE]') continue

                        try {
                            const parsed = JSON.parse(data)

                            if (currentEvent === 'session') {
                                onSessionUpdate(parsed.session_id)
                            } else if (currentEvent === 'message') {
                                onStreamMessage(parsed.content)
                            } else if (currentEvent === 'output') {
                                // Check for error messages in 'user' tag
                                if (parsed.tag === 'user' && parsed.data.startsWith('ERROR:')) {
                                    // Send error as a special error tag
                                    onStreamMessage(parsed.data, 'error')
                                } else {
                                    onStreamMessage(parsed.data, parsed.tag)
                                }
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e, 'Data:', data)
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error sending message:', error)
        } finally {
            setIsLoading(false)
            if (onLoadingChange) onLoadingChange(false)
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    return (
        <div className="chat-input-container">
            <form className="chat-input-form" onSubmit={handleSubmit}>
                <textarea
                    ref={textareaRef}
                    className="chat-input"
                    placeholder="Ask anything"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    rows={1}
                />
                <button
                    type="submit"
                    className="send-button"
                    disabled={!input.trim() || isLoading}
                >
                    <i className="fa fa-arrow-up"></i>
                </button>
            </form>
        </div>
    )
}

export default ChatInput
