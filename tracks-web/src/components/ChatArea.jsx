import { useEffect, useRef, useState } from 'react'
import Message from './Message'
import ChatInput from './ChatInput'
import './ChatArea.css'

function ChatArea({ messages, sessionId, onSendMessage, onStreamMessage, onSessionUpdate, utcOffset }) {
    const messagesEndRef = useRef(null)
    const [isResponseLoading, setIsResponseLoading] = useState(false)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, isResponseLoading])

    return (
        <div className="chat-area">
            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <h2>What can I help with?</h2>
                    </div>
                ) : (
                    <>
                        {messages.map((message, index) => (
                            <Message
                                key={index}
                                role={message.role}
                                content={message.content}
                                serialized_output={message.serialized_output}
                                timestamp={message.timestamp}
                                utcOffset={utcOffset}
                            />
                        ))}
                        {isResponseLoading && (
                            <div className="message assistant">
                                <div className="message-content">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>
            <ChatInput
                sessionId={sessionId}
                onSendMessage={onSendMessage}
                onStreamMessage={onStreamMessage}
                onSessionUpdate={onSessionUpdate}
                onLoadingChange={setIsResponseLoading}
            />
        </div>
    )
}

export default ChatArea
