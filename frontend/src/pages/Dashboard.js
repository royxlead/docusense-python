import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = ({ onNavigate, onSelectDocument }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/v1/documents');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/v1/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      setStats({
        total_documents: 0,
        categories: {},
        average_processing_time: 0
      });
    }
  };

  const handleDocumentClick = async (document) => {
    try {
      const response = await axios.get(`/api/v1/documents/${document.document_id}`);
      onSelectDocument(response.data);
      onNavigate('document');
    } catch (error) {
      console.error('Failed to fetch document details:', error);
      onSelectDocument(document);
      onNavigate('document');
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      legal: '⚖️',
      medical: '🏥',
      financial: '💰',
      technical: '🔧',
      business: '💼',
      academic: '🎓',
      administrative: '📋'
    };
    return icons[category] || '📄';
  };

  const formatProcessingTime = (seconds) => {
    return seconds ? `${seconds.toFixed(1)}s` : 'N/A';
  };

  const formatFileSize = (bytes) => {
    if (typeof bytes !== 'number' || isNaN(bytes)) return null;
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatCharCount = (n) => {
    if (typeof n !== 'number' || isNaN(n)) return null;
    if (n < 1000) return `${n} chars`;
    if (n < 1_000_000) return `${(n / 1000).toFixed(1)}K chars`;
    return `${(n / 1_000_000).toFixed(2)}M chars`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="dashboard fade-in" style={{ textAlign: 'center', padding: 'var(--space-16)' }}>
        <div className="loading-spinner"></div>
        <p style={{ marginTop: 'var(--space-4)', color: 'var(--gray-600)' }}>
          Loading your dashboard...
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard fade-in">
      <div className="page-header">
        <h1 className="page-title">DocuSense</h1>
        <p className="page-subtitle">
          Manage and analyze your documents with comprehensive AI-powered insights
        </p>
      </div>

      {/* Modern Statistics Grid */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats.total_documents}</div>
            <div className="stat-label">Total Documents</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Object.keys(stats.categories || {}).length}</div>
            <div className="stat-label">Categories</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{formatProcessingTime(stats.average_processing_time)}</div>
            <div className="stat-label">Avg Processing Time</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {stats.categories ? Math.max(...Object.values(stats.categories)) : 0}
            </div>
            <div className="stat-label">Most Common Type</div>
          </div>
        </div>
      )}

      {/* Documents Section */}
      <div style={{ marginTop: 'var(--space-12)' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: 'var(--space-8)' 
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: '600', 
            color: 'var(--gray-900)' 
          }}>
            Recent Documents
          </h2>
          <button
            onClick={() => onNavigate('upload')}
            className="btn btn-primary"
          >
            ➕ Upload New Document
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-16)' }}>
            <div style={{ fontSize: '4rem', marginBottom: 'var(--space-4)' }}>📄</div>
            <h3 style={{ 
              fontSize: '1.25rem', 
              fontWeight: '600', 
              marginBottom: 'var(--space-2)' 
            }}>
              No Documents Yet
            </h3>
            <p style={{ color: 'var(--gray-600)', marginBottom: 'var(--space-6)' }}>
              Upload your first document to get started with AI-powered analysis
            </p>
            <button
              onClick={() => onNavigate('upload')}
              className="btn btn-primary btn-lg"
            >
              🚀 Upload First Document
            </button>
          </div>
        ) : (
          <div className="document-grid">
            {documents.map(doc => (
              <div
                key={doc.document_id}
                className="document-card"
                onClick={() => handleDocumentClick(doc)}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  marginBottom: 'var(--space-4)' 
                }}>
                  <span style={{ fontSize: '1.5rem', marginRight: 'var(--space-3)' }}>
                    {getCategoryIcon(doc.classification?.category)}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ 
                      fontSize: '1.125rem', 
                      fontWeight: '600', 
                      marginBottom: 'var(--space-1)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {doc.file_name}
                    </h3>
                    <p style={{ 
                      color: 'var(--gray-600)', 
                      fontSize: '0.875rem',
                      textTransform: 'capitalize'
                    }}>
                      {doc.classification?.category || 'Unknown Category'}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2" style={{ gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: '500' }}>
                      ENTITIES
                    </span>
                    <p style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--gray-900)' }}>
                      {doc.entity_count || 0}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: '500' }}>
                      SIZE
                    </span>
                    <p style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--gray-900)' }}>
                      {(() => {
                        const byBytes = formatFileSize(doc.file_size_bytes ?? doc.size_bytes);
                        const byChars = formatCharCount(doc.text_length);
                        return byBytes || byChars || '—';
                      })()}
                    </p>
                  </div>
                </div>

                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  paddingTop: 'var(--space-3)',
                  borderTop: '1px solid var(--gray-200)'
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>
                    {formatDate(doc.processing_timestamp)}
                  </span>
                  <span className="btn btn-secondary" style={{ 
                    fontSize: '0.75rem', 
                    padding: 'var(--space-1) var(--space-3)' 
                  }}>
                    View Details →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
