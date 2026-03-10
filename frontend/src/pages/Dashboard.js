import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Briefcase, FileText, CheckSquare, Calendar, 
  ArrowRight, Clock 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { dashboardAPI } from '../lib/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
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
        <h1 className="text-3xl font-bold text-white mb-2">
          {t('dashboard.welcome')}, {user?.full_name || user?.username}
        </h1>
        <p className="text-gray-400">{t('dashboard.overview')}</p>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : (
        <>
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
                    className="stat-card block group"
                    data-testid={`stat-card-${index}`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${stat.color}`} />
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-white group-hover:translate-x-1 transition-all" />
                    </div>
                    <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                    <div className="text-gray-400 text-sm">{stat.label}</div>
                    {stat.total !== undefined && stat.total !== stat.value && (
                      <div className="text-gray-600 text-xs mt-1">
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
