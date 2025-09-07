import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="page-container">
          <div className="error-boundary">
            <div className="error-icon">⚠️</div>
            <h2 className="error-title">Oops! Something went wrong</h2>
            <p className="error-description">
              We encountered an unexpected error while loading this page. This has been logged and we're working on a fix.
            </p>
            
            <div className="error-actions">
              <button 
                onClick={() => this.setState({ hasError: false, error: null })}
                className="btn btn-primary"
              >
                🔄 Try Again
              </button>
              <button 
                onClick={() => window.location.href = '/'}
                className="btn btn-outline"
              >
                🏠 Go Home
              </button>
            </div>

            <details className="error-details">
              <summary className="error-details-summary">
                🔧 Technical Details (for developers)
              </summary>
              <div className="error-details-content">
                <pre className="error-stack">
                  {this.state.error?.toString()}
                </pre>
              </div>
            </details>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
