import { useState, useEffect, useRef } from 'react'
import './ChatInterface.css'
import MessageBubble from './MessageBubble'
import EligibilityCard from './EligibilityCard'
import DocumentUpload from './DocumentUpload'
import DecisionCard from './DecisionCard'

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentStage, setCurrentStage] = useState('greeting')
  const [userData, setUserData] = useState({})
  const [eligibilityData, setEligibilityData] = useState(null)
  const [uploadedDocs, setUploadedDocs] = useState([])
  const [finalDecision, setFinalDecision] = useState(null)
  const [sessionId] = useState(`session_${Date.now()}`)
  const [showEligibility, setShowEligibility] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, eligibilityData, finalDecision])

  useEffect(() => {
    addMessage(
      "👋 Hello! I'm your AI Loan Assistant powered by a Multi-Agent system. I can help you get a personal loan approved in just 3-5 minutes! What type of loan are you looking for today?",
      'assistant'
    )
  }, [])

  const addMessage = (content, role) => {
    setMessages(prev => [...prev, {
      content,
      role,
      timestamp: new Date()
    }])
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = inputValue.trim()
    addMessage(userMessage, 'user')
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        }),
        signal: AbortSignal.timeout(10000)
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()

      addMessage(data.message, 'assistant')
      setCurrentStage(data.stage)
      setUserData(data.user_data)

      // Check if we should show eligibility
      if (data.stage === 'eligibility' && !showEligibility) {
        setShowEligibility(true)
        setTimeout(() => {
          handleEligibilityCheck()
        }, 1500)
      }

    } catch (error) {
      console.error('Chat error:', error)
      if (error.name === 'TimeoutError') {
        addMessage('⚠️ Request timed out. Please check backend connection.', 'assistant')
      } else {
        addMessage('⚠️ Connection error. Ensure backend is running on http://localhost:5000', 'assistant')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleEligibilityCheck = async () => {
    addMessage('🔍 Analyzing your application with Multi-Agent AI...', 'assistant')
    
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000/api/eligibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId
        })
      })

      if (!response.ok) throw new Error('Eligibility check failed')

      const result = await response.json()
      setEligibilityData(result)

      if (result.eligible) {
        addMessage(
          `🎉 Great news! You're eligible for ₹${result.approved_amount.toLocaleString()} at ${result.interest_rate}% interest!`,
          'assistant'
        )
        
        setTimeout(() => {
          addMessage(
            '📄 Please upload these documents to complete your application:\n\n• Aadhaar Card\n• PAN Card\n• Latest Salary Slip',
            'assistant'
          )
          setCurrentStage('documents')
        }, 2000)
      } else {
        addMessage(
          `We can offer up to ₹${result.max_eligible.toLocaleString()}. Would you like to apply for this amount?`,
          'assistant'
        )
      }

    } catch (error) {
      console.error('Eligibility error:', error)
      addMessage('Failed to check eligibility. Please try again.', 'assistant')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file, type) => {
    console.log('📤 Uploading:', file.name, 'Type:', type)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    formData.append('session_id', sessionId)

    try {
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()
      console.log('📥 Upload response:', result)

      if (!response.ok || !result.verified) {
        throw new Error(result.error || 'Upload failed')
      }
      
      setUploadedDocs(prev => [...prev, result])
      addMessage(result.message, 'assistant')
      
      console.log('📊 Total docs uploaded:', uploadedDocs.length + 1)
      
      // Check if all 3 documents uploaded
      if (uploadedDocs.length + 1 >= 3) {
        console.log('✅ All 3 documents uploaded! Processing decision...')
        setTimeout(() => {
          addMessage('✅ All documents verified! Processing final decision with Decision Agent...', 'assistant')
          handleFinalDecision()
        }, 2000)
      }
    } catch (error) {
      console.error('❌ Upload error:', error)
      addMessage(`Failed to upload ${type}. ${error.message}`, 'assistant')
    }
  }

  const handleFinalDecision = async () => {
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000/api/decision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId
        })
      })

      if (!response.ok) throw new Error('Decision failed')

      const decision = await response.json()
      setFinalDecision(decision)
      setCurrentStage('complete')

    } catch (error) {
      console.error('Decision error:', error)
      addMessage('Failed to process decision. Please try again.', 'assistant')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadLetter = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/generate-letter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved_amount: eligibilityData?.approved_amount,
          interest_rate: eligibilityData?.interest_rate
        })
      })

      if (!response.ok) throw new Error('Failed to generate letter')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `loan_sanction_${Date.now()}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      addMessage('✅ Sanction letter downloaded!', 'assistant')
    } catch (error) {
      console.error('Download error:', error)
      addMessage('Failed to download letter.', 'assistant')
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>🏦 AI Loan Assistant</h2>
        <p>⚡ Powered by Multi-Agent AI • 🔒 Data processed securely</p>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {eligibilityData && (
          <EligibilityCard
            data={eligibilityData}
            userData={userData}
          />
        )}

        {currentStage === 'documents' && !finalDecision && (
          <DocumentUpload
            onUpload={handleFileUpload}
            uploadedDocs={uploadedDocs}
          />
        )}

        {finalDecision && (
          <DecisionCard
            decision={finalDecision}
            onDownload={handleDownloadLetter}
          />
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>AI Agents working...</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
          disabled={isLoading || currentStage === 'complete'}
          className="chat-input"
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !inputValue.trim() || currentStage === 'complete'}
          className="send-button"
        >
          Send
        </button>
      </div>

      <div className="chat-footer">
        <span>⚡ 3-5 min approval</span>
        <span>•</span>
        <span>🔒 RBI Compliant</span>
        <span>•</span>
        <span>✓ On-premises processing</span>
      </div>
    </div>
  )
}

export default ChatInterface