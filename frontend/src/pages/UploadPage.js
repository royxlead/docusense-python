import React, { useState, useRef } from 'react';
import axios from 'axios';

const UploadPage = ({ onNavigate }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      setSelectedFile(files[0]);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setUploadResult({
        success: true,
        message: 'Document uploaded and processed successfully!',
        data: response.data
      });
    } catch (error) {
      console.error('Upload error:', error);
      let errorMessage = 'Upload failed';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map(err => err.msg || err).join(', ');
        } else {
          errorMessage = 'Validation error occurred';
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setUploadResult({
        success: false,
        message: errorMessage,
        data: null
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="upload-page fade-in">
      <div className="page-header">
        <h1 className="page-title">Upload Your Document</h1>
        <p className="page-subtitle">
          Upload any document to extract insights with AI-powered analysis including OCR, 
          classification, summarization, and entity recognition.
        </p>
      </div>

      <div className="upload-container">
        <div className="card">
          <div className="card-content">
            {/* Modern Drag & Drop Upload Area */}
            <div 
              className={`upload-area ${dragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current.click()}
            >
              <div className="upload-icon">
                {selectedFile ? '📄' : '☁️'}
              </div>
              
              {selectedFile ? (
                <div className="selected-file">
                  <div className="upload-text">{selectedFile.name}</div>
                  <div className="upload-subtext">
                    {formatFileSize(selectedFile.size)} • Click to change file
                  </div>
                </div>
              ) : (
                <>
                  <div className="upload-text">
                    Drop your document here, or click to browse
                  </div>
                  <div className="upload-subtext">
                    Supports PDF, Word, Text, and Image files up to 50MB
                  </div>
                </>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.txt,.docx,.png,.jpg,.jpeg"
                style={{ display: 'none' }}
              />
            </div>

            {/* Upload Button */}
            {selectedFile && (
              <div style={{ marginTop: 'var(--space-6)', textAlign: 'center' }}>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className={`btn btn-primary btn-lg ${uploading ? 'loading' : ''}`}
                >
                  {uploading ? (
                    <>
                      <div className="loading-spinner" style={{ width: '20px', height: '20px' }}></div>
                      Processing Document...
                    </>
                  ) : (
                    <>
                      🚀 Upload & Analyze
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Results */}
            {uploadResult && (
              <div className={`alert ${uploadResult.success ? 'alert-success' : 'alert-error'}`}>
                <span>{uploadResult.success ? '✅' : '❌'}</span>
                <div>
                  <strong>{uploadResult.success ? 'Success!' : 'Error'}</strong>
                  <p>{uploadResult.message}</p>
                  {uploadResult.success && uploadResult.data && (
                    <div style={{ marginTop: 'var(--space-4)' }}>
                      <button
                        onClick={() => onNavigate('dashboard')}
                        className="btn btn-secondary"
                      >
                        View Dashboard
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-4" style={{ marginTop: 'var(--space-12)' }}>
          <div className="card">
            <div className="card-content" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🔍</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: 'var(--space-2)' }}>
                OCR Analysis
              </h3>
              <p style={{ color: 'var(--gray-600)', fontSize: '0.875rem' }}>
                Extract text from images and PDFs with high accuracy
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-content" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🏷️</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: 'var(--space-2)' }}>
                Smart Classification
              </h3>
              <p style={{ color: 'var(--gray-600)', fontSize: '0.875rem' }}>
                Automatically categorize documents using AI
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-content" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>📝</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: 'var(--space-2)' }}>
                AI Summarization
              </h3>
              <p style={{ color: 'var(--gray-600)', fontSize: '0.875rem' }}>
                Generate intelligent summaries with key insights
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-content" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 'var(--space-3)' }}>🎯</div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: 'var(--space-2)' }}>
                Entity Recognition
              </h3>
              <p style={{ color: 'var(--gray-600)', fontSize: '0.875rem' }}>
                Identify people, organizations, locations, and dates
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
