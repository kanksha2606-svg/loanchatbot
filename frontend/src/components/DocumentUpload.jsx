import { useState } from 'react'
import './DocumentUpload.css'

function DocumentUpload({ onUpload, uploadedDocs }) {
  const [uploading, setUploading] = useState({})

  const documents = [
    { type: 'aadhaar', label: '📇 Aadhaar Card', required: true },
    { type: 'pan', label: '💳 PAN Card', required: true },
    { type: 'salary', label: '💰 Salary Slip', required: true }
  ]

  const isUploaded = (type) => {
    return uploadedDocs.some(doc => doc.type === type)
  }

  const handleFileSelect = async (e, type) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate file
    const maxSize = 5 * 1024 * 1024 // 5MB
    if (file.size > maxSize) {
      alert('File too large. Maximum size is 5MB.')
      return
    }

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
    if (!validTypes.includes(file.type)) {
      alert('Invalid file type. Please upload JPG, PNG, or PDF.')
      return
    }

    // Set uploading state
    setUploading(prev => ({ ...prev, [type]: true }))

    try {
      // Call parent upload handler
      await onUpload(file, type)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    } finally {
      // Clear uploading state
      setUploading(prev => ({ ...prev, [type]: false }))
      // Reset file input
      e.target.value = ''
    }
  }

  return (
    <div className="document-upload-card">
      <div className="document-header">
        <h3>📄 Document Verification</h3>
        <p>Upload the following documents to complete your application</p>
      </div>

      <div className="document-list">
        {documents.map((doc) => {
          const uploaded = isUploaded(doc.type)
          const isUploading = uploading[doc.type]

          return (
            <div key={doc.type} className={`document-item ${uploaded ? 'uploaded' : ''}`}>
              <div className="document-info">
                <span className="document-label">{doc.label}</span>
                {doc.required && <span className="required-badge">Required</span>}
              </div>

              <div className="document-action">
                {uploaded ? (
                  <div className="upload-success">
                    <span className="success-icon">✓</span>
                    <span>Verified</span>
                  </div>
                ) : isUploading ? (
                  <div className="upload-loading">
                    <div className="spinner"></div>
                    <span>Uploading...</span>
                  </div>
                ) : (
                  <label className="upload-button">
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={(e) => handleFileSelect(e, doc.type)}
                      style={{ display: 'none' }}
                    />
                    <span>📤 Upload</span>
                  </label>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="document-footer">
        <p className="upload-note">
          ℹ️ Accepted formats: JPG, PNG, PDF (Max 5MB)
        </p>
        <div className="upload-progress">
          <span>{uploadedDocs.length} / 3 documents uploaded</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(uploadedDocs.length / 3) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default DocumentUpload