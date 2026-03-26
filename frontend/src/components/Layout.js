import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, FileText, Briefcase, Mail, Calendar, 
  CheckSquare, FileEdit, Bot, Settings, LogOut, Menu, X,
  Shield, Globe, ChevronRight, Sun, Moon, Brain, Activity
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'nav.dashboard' },
  { path: '/documents', icon: FileText, label: 'nav.documents' },
  { path: '/cases', icon: Briefcase, label: 'nav.cases' },
  { path: '/emails', icon: Mail, label: 'nav.emails' },
  { path: '/tasks', icon: CheckSquare, label: 'nav.tasks' },
  { path: '/calendar', icon: Calendar, label: 'nav.calendar' },
  { path: '/ai', icon: Bot, label: 'nav.aiChat' },
  { path: '/ai-knowledge', icon: Brain, label: 'KI-Wissen' },
  { path: '/health', icon: Activity, label: 'System-Status' },
  { path: '/settings', icon: Settings, label: 'nav.settings' },
];

export default function Layout() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Theme-aware classes
  const bgPrimary = theme === 'dark' ? 'bg-[#0A0A0A]' : 'bg-white';
  const bgSecondary = theme === 'dark' ? 'bg-[#121212]' : 'bg-gray-50';
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-gray-900';
  const textSecondary = theme === 'dark' ? 'text-gray-400' : 'text-gray-600';
  const textMuted = theme === 'dark' ? 'text-gray-600' : 'text-gray-400';
  const borderColor = theme === 'dark' ? 'border-white/5' : 'border-gray-200';

  return (
    <div className={`min-h-screen ${bgPrimary} flex`}>
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 ${bgPrimary} border-r ${borderColor}
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={`p-6 border-b ${borderColor}`}>
            <div className="flex items-center justify-between">
              <h1 className={`text-xl font-bold ${textPrimary} tracking-tight`}>CaseDesk AI</h1>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className={textSecondary}
                  onClick={toggleTheme}
                  data-testid="theme-toggle"
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`lg:hidden ${textSecondary}`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>
            <p className={`text-xs ${textMuted} mt-1`}>Self-Hosted v1.0.2</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
                    ${isActive 
                      ? theme === 'dark'
                        ? 'bg-white/10 text-white'
                        : 'bg-blue-50 text-blue-600'
                      : theme === 'dark'
                        ? 'text-gray-400 hover:text-white hover:bg-white/5'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                  data-testid={`nav-${item.path.replace('/', '') || 'dashboard'}`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{t(item.label)}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* User Section */}
          <div className={`p-4 border-t ${borderColor}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 ${theme === 'dark' ? 'bg-white/10' : 'bg-blue-100'} rounded-lg flex items-center justify-center ${textPrimary} font-medium`}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`${textPrimary} text-sm font-medium truncate`}>{user?.full_name || user?.username}</p>
                <p className={`${textMuted} text-xs truncate`}>{user?.email}</p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              className={`w-full justify-start ${textSecondary} hover:${textPrimary} ${theme === 'dark' ? 'hover:bg-white/5' : 'hover:bg-gray-100'}`}
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              {t('auth.logout')}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top Bar */}
        <header className={`sticky top-0 z-30 ${bgSecondary} border-b ${borderColor} px-4 py-3 lg:hidden`}>
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              className={textSecondary}
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </Button>
            <h1 className={`text-lg font-bold ${textPrimary}`}>CaseDesk AI</h1>
            <Button
              variant="ghost"
              size="sm"
              className={textSecondary}
              onClick={toggleTheme}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1">
          <Outlet />
        </main>

        {/* Footer */}
        <footer className={`border-t ${borderColor} px-6 py-4`}>
          <div className={`flex items-center justify-between text-xs ${textMuted}`}>
            <span>CaseDesk AI - Self-Hosted Document Management</span>
            <div className="flex items-center gap-2">
              <Shield className="w-3 h-3" />
              <span>Privacy-First</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
