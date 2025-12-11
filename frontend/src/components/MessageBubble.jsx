import './MessageBubble.css'

function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  
  return (
    <div className={`message-bubble ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-content">
        {!isUser && <span className="bot-icon">🤖</span>}
        <div className="message-text">{String(message.content)}</div>
      </div>
      <div className="message-time">
        {message.timestamp && message.timestamp.toLocaleTimeString ? 
          message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          }) : 
          new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })
        }
      </div>
    </div>
  )
}

export default MessageBubble