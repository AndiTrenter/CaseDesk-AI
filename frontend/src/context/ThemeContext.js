import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('casedesk-theme') || 'dark';
    }
    return 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
      // Dark theme CSS variables
      root.style.setProperty('--bg-primary', '#0A0A0A');
      root.style.setProperty('--bg-secondary', '#121212');
      root.style.setProperty('--bg-tertiary', '#1A1A1A');
      root.style.setProperty('--text-primary', '#FFFFFF');
      root.style.setProperty('--text-secondary', '#9CA3AF');
      root.style.setProperty('--text-muted', '#6B7280');
      root.style.setProperty('--border-color', 'rgba(255, 255, 255, 0.05)');
      root.style.setProperty('--border-hover', 'rgba(255, 255, 255, 0.1)');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
      // Light theme CSS variables
      root.style.setProperty('--bg-primary', '#FFFFFF');
      root.style.setProperty('--bg-secondary', '#F9FAFB');
      root.style.setProperty('--bg-tertiary', '#F3F4F6');
      root.style.setProperty('--text-primary', '#111827');
      root.style.setProperty('--text-secondary', '#4B5563');
      root.style.setProperty('--text-muted', '#9CA3AF');
      root.style.setProperty('--border-color', 'rgba(0, 0, 0, 0.05)');
      root.style.setProperty('--border-hover', 'rgba(0, 0, 0, 0.1)');
    }
    
    localStorage.setItem('casedesk-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
