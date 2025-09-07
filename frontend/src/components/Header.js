import React from 'react';

const Header = ({ currentPage, onNavigate }) => {
  const navItems = [
    { id: 'upload', label: 'Upload', icon: '📤' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'search', label: 'Search', icon: '🔍' }
  ];

  return (
    <header className="app-header">
      <div className="header-content">
        <h1 className="app-title">DocuSense</h1>
        <nav className="nav-menu">
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-button ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <span style={{ marginRight: 'var(--space-2)' }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default Header;
