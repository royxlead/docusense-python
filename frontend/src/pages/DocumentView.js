import React, { useState } from 'react';
import DocumentChat from '../components/DocumentChat';

const DocumentView = ({ document, onNavigate }) => {
  const [showChat, setShowChat] = useState(false);
  if (!document) {
    return (
      <div className="document-view">
        <h2>Document not found</h2>
        <button onClick={() => onNavigate('dashboard')}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="document-view">
      <div className="document-header">
        <h2>{document.file_name}</h2>
        <div className="header-buttons">
          <button 
            onClick={() => setShowChat(true)} 
            className="chat-button"
            title="Chat with AI about this document"
          >
            💬 Chat with AI
          </button>
          <button onClick={() => onNavigate('dashboard')} className="back-button">
            Back to Dashboard
          </button>
        </div>
      </div>
      
      <div className="document-content">
        <div className="document-section">
          <h3>Classification</h3>
          <div className="classification-info">
            <p>Category: <strong>{document.classification?.category || 'Unknown'}</strong></p>
            <p>Confidence: <strong>{((document.classification?.confidence || 0) * 100).toFixed(1)}%</strong></p>
          </div>
        </div>
        
        <div className="document-section">
          <h3>Summary</h3>
          <div className="summary-content">
            <p>{document.summary || 'No summary available.'}</p>
          </div>
        </div>
        
        <div className="document-section">
          <h3>Named Entities</h3>
          <div className="entities-content">
            {document.entities ? (
              Object.entries(document.entities).map(([type, entities]) => (
                <div key={type} className="entity-group">
                  <h4>{type}</h4>
                  <div className="entity-list">
                    {Array.isArray(entities) ? entities.map((entity, index) => (
                      <span key={index} className="entity-tag">
                        {typeof entity === 'string' ? entity : (entity.text || entity.name || JSON.stringify(entity))}
                      </span>
                    )) : (
                      <span className="entity-tag">
                        {typeof entities === 'string' ? entities : JSON.stringify(entities)}
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p>No entities extracted.</p>
            )}
          </div>
        </div>
        
        <div className="document-section">
          <h3>Document Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <label>Text Length:</label>
              <span>{document.text_length || 0} characters</span>
            </div>
            <div className="stat-item">
              <label>Entity Count:</label>
              <span>{document.entity_count || 0} entities</span>
            </div>
            <div className="stat-item">
              <label>Processing Time:</label>
              <span>{document.processing_time_seconds || 0}s</span>
            </div>
            <div className="stat-item">
              <label>Processed:</label>
              <span>{document.processing_timestamp ? new Date(document.processing_timestamp).toLocaleString() : 'Unknown'}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Gemini AI Chat Component */}
      {showChat && (
        <DocumentChat 
          document={document}
          onClose={() => setShowChat(false)}
        />
      )}
    </div>
  );
};

export default DocumentView;
