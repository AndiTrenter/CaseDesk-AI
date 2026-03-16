import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Briefcase, FileText, CheckSquare, Calendar, 
  ArrowRight, Clock, Sparkles, AlertTriangle, Lightbulb,
  RefreshCw, ChevronRight, Bell
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { dashboardAPI, aiAPI } from '../lib/api';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { theme } = useTheme();
  const [stats, setStats] = useState(null);
  const [briefing, setBriefing] = useState(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [loading, setLoading] = useState(true);

  // Theme-aware classes
  const bgCard = theme === 'dark' ? 'bg-[#121212]' : 'bg-white';
  const borderColor = theme === 'dark' ? 'border-white/5' : 'border-gray-200';
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-gray-900';
  const textSecondary = theme === 'dark' ? 'text-gray-400' : 'text-gray-600';
  const textMuted = theme === 'dark' ? 'text-gray-500' : 'text-gray-400';

  useEffect(() => {
    loadStats();
    loadDailyBriefing();
  }, []);

  const loadStats = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
    setLoading(false);
  };

  const loadDailyBriefing = async () => {
    setLoadingBriefing(true);
    try {
      const response = await aiAPI.dailyBriefing();
      if (response.data.success) {
        setBriefing(response.data);
      }
    } catch (error) {
      console.error('Failed to load briefing:', error);
    }
    setLoadingBriefing(false);
  };

  const statCards = [
    {
      label: t('dashboard.openCases'),
      value: stats?.cases?.open || 0,
      total: stats?.cases?.total || 0,
      icon: Briefcase,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      link: '/cases'
    },
    {
      label: t('dashboard.totalDocuments'),
      value: stats?.documents?.total || 0,
      icon: FileText,
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      link: '/documents'
    },
    {
      label: t('dashboard.pendingTasks'),
      value: stats?.tasks?.pending || 0,
      icon: CheckSquare,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      link: '/tasks'
    },
    {
      label: t('dashboard.upcomingEvents'),
      value: stats?.upcoming_events?.length || 0,
      icon: Calendar,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
      link: '/calendar'
    }
  ];

  return (
    <div className="page-container" data-testid="dashboard-page">
      {/* Welcome Header */}
      <motion.div 
        className="mb-8"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={`text-3xl font-bold ${textPrimary} mb-2`}>
          {t('dashboard.welcome')}, {user?.full_name || user?.username}
        </h1>
        <p className={textSecondary}>{t('dashboard.overview')}</p>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : (
        <>
          {/* AI Daily Briefing */}
          {briefing && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`${bgCard} border ${borderColor} rounded-xl p-6 mb-8`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h2 className={`font-semibold ${textPrimary}`}>KI-Tagesbriefing</h2>
                    <p className={`text-sm ${textMuted}`}>{briefing.date}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={loadDailyBriefing}
                  disabled={loadingBriefing}
                  className={textSecondary}
                >
                  <RefreshCw className={`w-4 h-4 ${loadingBriefing ? 'animate-spin' : ''}`} />
                </Button>
              </div>
              
              <div className="space-y-4">
                {/* Greeting */}
                {briefing.briefing?.begruessung && (
                  <p className={textSecondary}>{briefing.briefing.begruessung}</p>
                )}
                
                {/* Today's Priorities */}
                {briefing.briefing?.prioritaeten_heute?.length > 0 && (
                  <div>
                    <h3 className={`text-sm font-medium ${textPrimary} mb-2 flex items-center gap-2`}>
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Prioritäten heute
                    </h3>
                    <div className="space-y-2">
                      {briefing.briefing.prioritaeten_heute.slice(0, 3).map((item, i) => (
                        <div key={i} className={`flex items-start gap-2 text-sm ${textSecondary}`}>
                          <ChevronRight className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <span>{item.item} {item.grund && <span className={textMuted}>- {item.grund}</span>}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Upcoming Deadlines */}
                {briefing.briefing?.anstehende_fristen?.length > 0 && (
                  <div>
                    <h3 className={`text-sm font-medium ${textPrimary} mb-2 flex items-center gap-2`}>
                      <Clock className="w-4 h-4 text-red-400" />
                      Anstehende Fristen
                    </h3>
                    <div className="space-y-2">
                      {briefing.briefing.anstehende_fristen.slice(0, 3).map((item, i) => (
                        <div key={i} className={`flex items-start gap-2 text-sm ${textSecondary}`}>
                          <Bell className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-400" />
                          <span>{item.frist}: {item.beschreibung}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Tip of the Day */}
                {briefing.briefing?.tipp_des_tages && (
                  <div className={`p-3 rounded-lg ${theme === 'dark' ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-blue-50 border border-blue-200'}`}>
                    <div className="flex items-start gap-2">
                      <Lightbulb className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <p className={`text-sm ${theme === 'dark' ? 'text-blue-300' : 'text-blue-700'}`}>
                        {briefing.briefing.tipp_des_tages}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
          
          {/* Loading Briefing Indicator */}
          {loadingBriefing && !briefing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`${bgCard} border ${borderColor} rounded-xl p-6 mb-8`}
            >
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 text-purple-400 animate-spin" />
                <span className={textSecondary}>KI-Briefing wird geladen...</span>
              </div>
            </motion.div>
          )}

          {/* Stat Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {statCards.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link
                    to={stat.link}
                    className={`block ${bgCard} border ${borderColor} rounded-xl p-5 hover:border-white/10 transition-all group`}
                    data-testid={`stat-card-${index}`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${stat.color}`} />
                      </div>
                      <ArrowRight className={`w-5 h-5 ${textMuted} group-hover:${textPrimary} group-hover:translate-x-1 transition-all`} />
                    </div>
                    <div className={`text-3xl font-bold ${textPrimary} mb-1`}>{stat.value}</div>
                    <div className={`${textSecondary} text-sm`}>{stat.label}</div>
                    {stat.total !== undefined && stat.total !== stat.value && (
                      <div className={`${textMuted} text-xs mt-1`}>
                        {stat.total} total
                      </div>
                    )}
                  </Link>
                </motion.div>
              );
            })}
          </div>

          {/* Recent Activity Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Documents */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">{t('dashboard.recentDocuments')}</h2>
                <Link to="/documents" className="text-sm text-gray-400 hover:text-white transition-colors">
                  {t('common.actions')} →
                </Link>
              </div>
              
              {stats?.recent_documents?.length > 0 ? (
                <div className="space-y-3">
                  {stats.recent_documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <FileText className="w-5 h-5 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm truncate">{doc.original_filename}</p>
                        <p className="text-gray-500 text-xs">{doc.document_type}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {t('dashboard.noData')}
                </div>
              )}
            </motion.div>

            {/* Urgent Tasks */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">{t('dashboard.urgentTasks')}</h2>
                <Link to="/tasks" className="text-sm text-gray-400 hover:text-white transition-colors">
                  {t('common.actions')} →
                </Link>
              </div>
              
              {stats?.urgent_tasks?.length > 0 ? (
                <div className="space-y-3">
                  {stats.urgent_tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                    >
                      <CheckSquare className={`w-5 h-5 ${
                        task.priority === 'urgent' ? 'text-red-400' :
                        task.priority === 'high' ? 'text-amber-400' : 'text-gray-400'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm truncate">{task.title}</p>
                        {task.due_date && (
                          <p className="text-gray-500 text-xs flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(task.due_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {t('dashboard.noData')}
                </div>
              )}
            </motion.div>
          </div>
        </>
      )}
    </div>
  );
}
