import './DecisionCard.css'

function DecisionCard({ decision, onDownload, onRetry }) {
  if (!decision) return null

  const isApproved = decision.status === 'approved'
  const isPending = decision.status === 'pending'
  const isRejected = decision.status === 'rejected' || decision.status === 'manual_review'
  const hasError = !!decision.error

  return (
    <div className={`decision-card ${isApproved ? 'approved' : isRejected ? 'rejected' : 'pending'}`}>
      <div className="decision-header">
        {hasError ? (
          <>
            <div className="decision-icon error">⚠️</div>
            <h2>Processing Error</h2>
          </>
        ) : isApproved ? (
          <>
            <div className="decision-icon success">🎉</div>
            <h2>Loan Approved!</h2>
          </>
        ) : isPending ? (
          <>
            <div className="decision-icon pending">⏳</div>
            <h2>Processing...</h2>
          </>
        ) : (
          <>
            <div className="decision-icon review">📋</div>
            <h2>Manual Review Required</h2>
          </>
        )}
      </div>

      <div className="decision-body">
        {hasError ? (
          <p className="decision-message error-message">
            {decision.message || decision.error || 'An error occurred while processing your application.'}
          </p>
        ) : (
          <p className="decision-message">
            {decision.decision || decision.message}
          </p>
        )}

        {decision.processing_time && (
          <div className="processing-stats">
            <div className="stat-item">
              <span className="stat-label">Processing Time:</span>
              <span className="stat-value highlight">{decision.processing_time}</span>
            </div>
            {decision.traditional_time && (
              <div className="stat-item">
                <span className="stat-label">Traditional Time:</span>
                <span className="stat-value">{decision.traditional_time}</span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="decision-footer">
        {hasError && onRetry ? (
          <button className="retry-button" onClick={onRetry}>
            🔄 Retry Decision
          </button>
        ) : isApproved && onDownload ? (
          <button className="download-button" onClick={onDownload}>
            📥 Download Sanction Letter
          </button>
        ) : null}
      </div>

      {isApproved && (
        <div className="approval-banner">
          <p>✨ Congratulations! Your loan has been processed using Multi-Agent AI in record time!</p>
        </div>
      )}
    </div>
  )
}

export default DecisionCard