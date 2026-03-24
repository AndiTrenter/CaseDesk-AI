import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import './i18n';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { setupAPI } from './lib/api';

// Pages
import SetupWizard from './pages/SetupWizard';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Cases from './pages/Cases';
import CaseDetail from './pages/CaseDetail';
import Tasks from './pages/Tasks';
import Calendar from './pages/Calendar';
import Emails from './pages/Emails';
import AIChat from './pages/AIChat';
import Settings from './pages/Settings';
import Layout from './components/Layout';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const AppRoutes = () => {
  const [setupStatus, setSetupStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    checkSetup();
  }, []);

  const checkSetup = async () => {
    try {
      const response = await setupAPI.getStatus();
      setSetupStatus(response.data);
    } catch (error) {
      console.error('Failed to check setup status:', error);
      setSetupStatus({ setup_completed: false, has_admin: false });
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-2 border-white/20 border-t-white rounded-full mx-auto mb-4" />
          <p className="text-gray-400">Loading CaseDesk AI...</p>
        </div>
      </div>
    );
  }

  // Show setup wizard if not configured (has_admin or is_configured)
  if (!setupStatus?.is_configured && !setupStatus?.has_admin) {
    return <SetupWizard onComplete={() => checkSetup()} />;
  }

  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/" replace /> : <Login />
      } />
      <Route path="/register/:token" element={<Register />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Dashboard />} />
        <Route path="documents" element={<Documents />} />
        <Route path="cases" element={<Cases />} />
        <Route path="cases/:caseId" element={<CaseDetail />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="emails" element={<Emails />} />
        <Route path="ai" element={<AIChat />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function ThemedToaster() {
  const { theme } = useTheme();
  
  return (
    <Toaster 
      position="top-right" 
      theme={theme}
      toastOptions={{
        style: theme === 'dark' ? {
          background: '#1A1A1A',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#EDEDED'
        } : {
          background: '#FFFFFF',
          border: '1px solid rgba(0,0,0,0.1)',
          color: '#111827'
        }
      }}
    />
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <ThemedToaster />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
