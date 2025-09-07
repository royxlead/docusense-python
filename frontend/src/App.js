import React, { useState } from 'react';
import './App.css';

// Component imports (these would be created in components/ folder)
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import UploadPage from './pages/UploadPage';
import Dashboard from './pages/Dashboard';
import SearchPage from './pages/SearchPage';
import DocumentView from './pages/DocumentView';

function App() {
  const [currentPage, setCurrentPage] = useState('upload');
  const [selectedDocument, setSelectedDocument] = useState(null);

  const renderPage = () => {
    switch (currentPage) {
      case 'upload':
        return <UploadPage onNavigate={setCurrentPage} />;
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentPage} onSelectDocument={setSelectedDocument} />;
      case 'search':
        return <SearchPage onNavigate={setCurrentPage} onSelectDocument={setSelectedDocument} />;
      case 'document':
        return <DocumentView document={selectedDocument} onNavigate={setCurrentPage} />;
      default:
        return <UploadPage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="App">
      <Header currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="main-content">
        <ErrorBoundary>
          {renderPage()}
        </ErrorBoundary>
      </main>
    </div>
  );
}

export default App;