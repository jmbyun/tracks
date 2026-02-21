import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './Message.css'

function ThinkingBlock({ content }) {
    const [isOpen, setIsOpen] = useState(false)
    return (
        <div className="block-container thinking">
            <div className="block-header" onClick={() => setIsOpen(!isOpen)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <i className="fa fa-lightbulb-o"></i>
                    <span className="block-title">Thinking Process</span>
                </div>
                <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
            </div>
            {isOpen && <div className="block-content">{content}</div>}
        </div>
    )
}

function ExecBlock({ content }) {
    return (
        <div className="block-container exec">
            <div className="block-header">
                <span className="block-label">EXECUTE</span>
            </div>
            <div className="block-content code">{content}</div>
        </div>
    )
}

function TerminalBlock({ content, type }) {
    const [isOpen, setIsOpen] = useState(false)
    const label = type === 'stderr' ? 'Warning' : 'Command Output'

    return (
        <div className={`block-container terminal ${type}`}>
            <div className="block-header" onClick={() => setIsOpen(!isOpen)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <i className="fa fa-terminal"></i>
                    <span className="block-title">{label}</span>
                </div>
                <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
            </div>
            {isOpen && <div className="block-content code">{content}</div>}
        </div>
    )
}


function DiffBlock({ content, className, ...props }) {
    const [isExpanded, setIsExpanded] = useState(false)

    // Parse diff content
    const lines = content.split('\n')
    let filename = 'Unknown file'
    let additions = 0
    let deletions = 0

    // Try to extract filename
    const diffLine = lines.find(l => l.startsWith('diff --git'))
    if (diffLine) {
        // diff --git a/path/to/file b/path/to/file
        // We want the part after b/
        const parts = diffLine.split(' b/')
        if (parts.length >= 2) {
            filename = parts[1].trim()
        }
    } else {
        const plusLine = lines.find(l => l.startsWith('+++ b/'))
        if (plusLine) filename = plusLine.substring(6).trim()
    }

    // Count stats
    lines.forEach(line => {
        if (line.startsWith('+') && !line.startsWith('+++')) additions++
        if (line.startsWith('-') && !line.startsWith('---')) deletions++
    })

    return (
        <div className={`block-container diff ${isExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="block-header" onClick={() => setIsExpanded(!isExpanded)}>
                <div className="diff-info">
                    <i className="fa fa-file-code-o"></i>
                    <span className="filename">{filename}</span>
                </div>
                <div className="diff-stats">
                    {additions > 0 && <span className="stat-added">+{additions}</span>}
                    {deletions > 0 && <span className="stat-removed">-{deletions}</span>}
                    <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
                </div>
            </div>
            {isExpanded && (
                <div className="block-content code">
                    <pre>
                        <code className={className} {...props}>
                            {content}
                        </code>
                    </pre>
                </div>
            )}
        </div>
    )
}

function SummarizeBlock({ content, components }) {
    const [isOpen, setIsOpen] = useState(false)
    return (
        <div className="block-container thinking">
            <div className="block-header" onClick={() => setIsOpen(!isOpen)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <i className="fa fa-file-text-o"></i>
                    <span className="block-title">Summarize</span>
                </div>
                <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
            </div>
            {isOpen && (
                <div className="block-content">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={components}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
            )}
        </div>
    )
}

function ExecutionBlock({ command, output, duration }) {
    const [isOutputOpen, setIsOutputOpen] = useState(false)
    const hasOutput = output && output.trim().length > 0

    // Parse command for display
    const parseCommand = (cmd) => {
        const trimmed = cmd.trim()

        // Handle heredoc file writes: cat << 'EOF' > /path/to/file
        const heredocMatch = trimmed.match(/^cat\s+<<\s*['"]?(\w+)['"]?\s*>\s*(.+)$/m)
        if (heredocMatch) {
            const filePath = heredocMatch[2].trim()
            return {
                displayText: `Write to ${filePath}`,
                isFileWrite: true,
                filePath
            }
        }

        // Handle simple file write with echo
        const echoMatch = trimmed.match(/^echo\s+.*\s*>\s*(.+)$/m)
        if (echoMatch) {
            const filePath = echoMatch[1].trim()
            return {
                displayText: `Write to ${filePath}`,
                isFileWrite: true,
                filePath
            }
        }

        // Truncate long commands at first newline for display
        const firstLine = trimmed.split('\n')[0]
        return {
            displayText: firstLine.length > 100 ? firstLine.substring(0, 100) + '...' : firstLine,
            isFileWrite: false
        }
    }

    const parsedCommand = parseCommand(command)

    return (
        <div className="block-container execution">
            <div
                className="block-header"
                onClick={() => hasOutput && setIsOutputOpen(!isOutputOpen)}
                style={{ cursor: hasOutput ? 'pointer' : 'default' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="block-label" style={{ fontWeight: 600 }}>EXECUTE</span>
                    {duration && <span className="execution-duration" style={{ opacity: 0.7 }}>({duration})</span>}
                </div>
                {hasOutput && (
                    <span className="toggle-icon">{isOutputOpen ? '▼' : '▶'}</span>
                )}
            </div>
            <div className="execution-command">
                <code className="command-text">{parsedCommand.displayText}</code>
            </div>
            {hasOutput && isOutputOpen && (
                <div className="block-content code">
                    {output}
                </div>
            )}
        </div>
    )
}

function formatLocalTime(isoString, utcOffset = 9) {
    if (!isoString) return ''
    const date = new Date(isoString)

    // Fallback to 9 if utcOffset is null/undefined
    const offset = (utcOffset === null || utcOffset === undefined) ? 9 : utcOffset

    // Format to target timezone using Etc/GMT syntax
    // Note: Etc/GMT signs are reversed (Etc/GMT-9 is UTC+9)
    const tzName = `Etc/GMT${offset >= 0 ? '-' : '+'}${Math.abs(offset)}`

    const options = {
        timeZone: tzName,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }

    try {
        return new Intl.DateTimeFormat('sv-SE', options).format(date)
    } catch (e) {
        console.error('Timezone format error:', e)
        // Fallback to system local if Etc/GMT fails
        return new Intl.DateTimeFormat('sv-SE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).format(date)
    }
}

function Message({ role, content, serialized_output, timestamp, utcOffset }) {
    const components = {
        // Custom rendering for code blocks
        code({ node, inline, className, children, ...props }) {
            const content = String(children).replace(/\n$/, '')
            const hasNewlines = content.includes('\n')

            // Check for diff language or signature
            const match = /language-(\w+)/.exec(className || '')
            const lang = match ? match[1] : ''
            const isDiff = lang === 'diff' || content.trim().startsWith('diff --git') || content.trim().startsWith('--- a/')

            if (!inline && isDiff) {
                return <DiffBlock content={content} className={className} {...props} />
            }

            // Force inline if no newlines (single line code)
            const isInline = inline || !hasNewlines

            return isInline ? (
                <code className="inline-code" {...props}>
                    {children}
                </code>
            ) : (
                <pre>
                    <code className={className} {...props}>
                        {children}
                    </code>
                </pre>
            )
        }
    }

    const renderContent = () => {
        if (role === 'assistant' && serialized_output && serialized_output.length > 0) {
            // Pass 1: Group consecutive items by tag
            const rawGroups = []
            let currentGroup = null

            serialized_output.forEach(item => {
                // Skip non-display tags
                if (['meta', 'user', 'title', 'tokens_used', 'done', 'session'].includes(item.tag)) return

                if (currentGroup && currentGroup.tag === item.tag) {
                    currentGroup.data += item.data
                } else {
                    if (currentGroup) rawGroups.push(currentGroup)
                    currentGroup = { ...item }
                }
            })
            if (currentGroup) rawGroups.push(currentGroup)

            // Pass 2: Merge execution related blocks (exec -> exec_output/stderr -> exec_time)
            const groups = []
            let currentExec = null

            rawGroups.forEach(item => {
                if (item.tag === 'exec') {
                    if (currentExec) groups.push(currentExec)
                    currentExec = {
                        tag: 'execution_group',
                        command: item.data,
                        output: '',
                        duration: null
                    }
                } else if ((item.tag === 'exec_output' || item.tag === 'stderr') && currentExec) {
                    currentExec.output += item.data
                } else if (item.tag === 'exec_time' && currentExec) {
                    currentExec.duration = item.data
                } else {
                    if (currentExec) {
                        groups.push(currentExec)
                        currentExec = null
                    }
                    groups.push(item)
                }
            })
            if (currentExec) groups.push(currentExec)

            return groups.map((item, index) => {
                switch (item.tag) {
                    case 'thinking':
                        return <ThinkingBlock key={index} content={item.data} />
                    case 'execution_group':
                        return <ExecutionBlock
                            key={index}
                            command={item.command}
                            output={item.output}
                            duration={item.duration}
                        />
                    case 'file_update':
                        return <DiffBlock key={index} content={item.data} />
                    case 'stdout':
                        return (
                            <ReactMarkdown
                                key={index}
                                remarkPlugins={[remarkGfm]}
                                components={components}
                            >
                                {item.data}
                            </ReactMarkdown>
                        )
                    case 'stderr':
                    case 'exec_output':
                        // Fallback for orphan outputs
                        return <TerminalBlock key={index} content={item.data} type={item.tag} />
                    case 'agent':
                        return <SummarizeBlock key={index} content={item.data} components={components} />
                    case 'error':
                        // Display error messages prominently
                        return (
                            <div key={index} className="error-message">
                                <i className="fa fa-exclamation-circle"></i>
                                <span>{item.data}</span>
                            </div>
                        )
                    default:
                        // Fallback for unknown tags or just plain text
                        return <div key={index} className="message-text">{item.data}</div>
                }
            })
        }

        // Fallback or User message
        if (role === 'assistant') {
            return (
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={components}
                >
                    {content}
                </ReactMarkdown>
            )
        }

        return <div className="message-text">{content}</div>
    }

    return (
        <div className={`message ${role}`}>
            <div className="message-wrapper">
                <div className="message-content">
                    {renderContent()}
                </div>
                {role === 'user' && timestamp && (
                    <div className="message-timestamp">
                        {formatLocalTime(timestamp, utcOffset)}
                    </div>
                )}
            </div>
        </div>
    )
}

export default Message
