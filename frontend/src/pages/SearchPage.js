import React, { useState } from 'react';
import axios from 'axios';

const SearchPage = ({ onNavigate, onSelectDocument }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setSearching(true);
    setSearchPerformed(true);

    try {
      const response = await axios.get(`/api/v1/search?query=${encodeURIComponent(query)}&k=10`);
      setResults(response.data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]); // Show empty results instead of dummy data
    } finally {
      setSearching(false);
    }
  };

  const handleResultClick = (result) => {
    onSelectDocument(result);
    onNavigate('document');
  };

  return (
    <div className="page-container">
      <div className="page-header text-center">
        <h1 className="page-title">🔍 Document Search</h1>
        <p className="page-subtitle">
          Find relevant information across all your documents using semantic search
        </p>
      </div>
      
      <div className="card">
        <div className="search-container">
          <div className="search-input-group">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documents... (e.g., 'expense reports 2024', 'technical documentation')"
              className="form-input search-input"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={!query.trim() || searching}
              className={`btn btn-primary search-btn ${searching ? 'loading' : ''}`}
            >
              {searching ? (
                <>
                  <span className="spinner"></span>
                  Searching...
                </>
              ) : (
                <>
                  🔍 Search
                </>
              )}
            </button>
          </div>
          
          {query.trim() && (
            <div className="search-tips">
              <p>💡 <strong>Pro tip:</strong> Try searching for concepts, topics, or specific terms that appear in your documents</p>
            </div>
          )}
        </div>
      </div>
      
      {searchPerformed && (
        <div className="search-results-section">
          <div className="results-header">
            <h3>Search Results</h3>
            <span className="results-count">{results.length} document{results.length !== 1 ? 's' : ''} found</span>
          </div>
          
          {results.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h4>No documents found</h4>
              <p>Try adjusting your search terms or uploading more documents to expand your search base.</p>
              <button onClick={() => onNavigate('upload')} className="btn btn-outline">
                📤 Upload Documents
              </button>
            </div>
          ) : (
            <div className="results-grid">
              {results.map(result => (
                <div
                  key={result.document_id}
                  className="result-card"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="result-header">
                    <div className="result-title">
                      <h4>{result.file_name || 'Untitled Document'}</h4>
                      <span className="similarity-badge">
                        {(result.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                  </div>
                  
                  <p className="result-summary">
                    {typeof result.summary === 'string' 
                      ? result.summary.length > 150 
                        ? result.summary.substring(0, 150) + '...'
                        : result.summary
                      : 'No summary available'
                    }
                  </p>
                  
                  <div className="result-meta">
                    <div className="meta-item">
                      <span className="meta-label">Category:</span>
                      <span className="meta-value">{result.classification?.category || 'Unknown'}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Confidence:</span>
                      <span className="meta-value">{((result.classification?.confidence || 0) * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  
                  <div className="result-action">
                    <span className="view-prompt">👆 Click to view document</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchPage;
