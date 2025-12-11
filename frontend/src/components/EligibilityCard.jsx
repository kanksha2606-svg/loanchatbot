import React from 'react';
import './EligibilityCard.css';

const EligibilityCard = ({ data }) => {
  return (
    <div className="eligibility-card">
      <div className="card-header">
        <h3>Eligibility Assessment</h3>
        <span className={`status ${data.eligible ? 'approved' : 'pending'}`}>
          {data.eligible ? '✓ Eligible' : 'Under Review'}
        </span>
      </div>
      
      <div className="card-body">
        <div className="info-row">
          <span className="label">Loan Amount:</span>
          <span className="value">₹{data.loanAmount?.toLocaleString('en-IN')}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Monthly Income:</span>
          <span className="value">₹{data.monthlyIncome?.toLocaleString('en-IN')}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Credit Score:</span>
          <span className="value score">{data.creditScore || 750}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Risk Level:</span>
          <span className={`value risk ${data.riskLevel?.toLowerCase()}`}>
            {data.riskLevel || 'Low'}
          </span>
        </div>
        
        <div className="info-row">
          <span className="label">Approval Probability:</span>
          <span className="value probability">{data.approvalProbability || 85}%</span>
        </div>
      </div>
      
      <div className="card-footer">
        <p className="processing-time">⚡ Processed in {data.processingTime || '2 minutes 34 seconds'}</p>
      </div>
    </div>
  );
};

export default EligibilityCard;