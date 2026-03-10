import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, Globe, Shield, Brain, 
  User, Moon, Sun, Check, AlertTriangle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { settingsAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

export default function Settings() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [systemSettings, setSystemSettings] = useState({
    ai_provider: 'disabled',
    openai_api_key: '',
    internet_access: 'denied',
    default_language: 'de'
  });
  
  const [userSettings, setUserSettings] = useState({
    language: 'de',
    theme: 'dark',
    notifications_enabled: true
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // Load user settings
      const userRes = await settingsAPI.getUser();
      if (userRes.data) {
        setUserSettings({
          language: userRes.data.language || 'de',
          theme: userRes.data.theme || 'dark',
          notifications_enabled: userRes.data.notifications_enabled ?? true
        });
      }
      
      // Load system settings if admin
      if (user?.role === 'admin') {
        const sysRes = await settingsAPI.getSystem();
        if (sysRes.data) {
          setSystemSettings({
            ai_provider: sysRes.data.ai_provider || 'disabled',
            openai_api_key: sysRes.data.openai_api_key || '',
            internet_access: sysRes.data.internet_access || 'denied',
            default_language: sysRes.data.default_language || 'de'
          });
        }
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
    setLoading(false);
  };

  const handleSaveUserSettings = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateUser(userSettings);
      i18n.changeLanguage(userSettings.language);
      
      // Apply theme
      if (userSettings.theme === 'light') {
        document.documentElement.classList.add('light');
      } else {
        document.documentElement.classList.remove('light');
      }
      
      toast.success(t('settings.saved'));
    } catch (error) {
      toast.error('Failed to save settings');
    }
    setSaving(false);
  };

  const handleSaveSystemSettings = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateSystem(systemSettings);
      toast.success(t('settings.saved'));
    } catch (error) {
      toast.error('Failed to save settings');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  return (
    <div className="page-container" data-testid="settings-page">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">{t('settings.title')}</h1>
          <p className="text-gray-400 text-sm">Manage your preferences and system configuration</p>
        </div>

        <Tabs defaultValue="user" className="space-y-6">
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger value="user" className="data-[state=active]:bg-white/10">
              <User className="w-4 h-4 mr-2" />
              {t('settings.user')}
            </TabsTrigger>
            {user?.role === 'admin' && (
              <>
                <TabsTrigger value="ai" className="data-[state=active]:bg-white/10">
                  <Brain className="w-4 h-4 mr-2" />
                  {t('settings.ai')}
                </TabsTrigger>
                <TabsTrigger value="privacy" className="data-[state=active]:bg-white/10">
                  <Shield className="w-4 h-4 mr-2" />
                  {t('settings.privacy')}
                </TabsTrigger>
              </>
            )}
          </TabsList>

          {/* User Settings */}
          <TabsContent value="user">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6 space-y-6"
            >
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">{t('settings.user')}</h3>
                
                <div className="space-y-4">
                  {/* Language */}
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-white">{t('settings.language')}</Label>
                      <p className="text-gray-500 text-sm">Choose your preferred language</p>
                    </div>
                    <Select
                      value={userSettings.language}
                      onValueChange={(value) => setUserSettings({ ...userSettings, language: value })}
                    >
                      <SelectTrigger className="w-40 bg-black/30 border-white/10 text-white" data-testid="language-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A] border-white/10">
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="de">Deutsch</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Theme */}
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-white">{t('settings.theme')}</Label>
                      <p className="text-gray-500 text-sm">Select your color scheme</p>
                    </div>
                    <Select
                      value={userSettings.theme}
                      onValueChange={(value) => setUserSettings({ ...userSettings, theme: value })}
                    >
                      <SelectTrigger className="w-40 bg-black/30 border-white/10 text-white" data-testid="theme-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A] border-white/10">
                        <SelectItem value="dark">
                          <span className="flex items-center gap-2">
                            <Moon className="w-4 h-4" /> {t('settings.dark')}
                          </span>
                        </SelectItem>
                        <SelectItem value="light">
                          <span className="flex items-center gap-2">
                            <Sun className="w-4 h-4" /> {t('settings.light')}
                          </span>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Notifications */}
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-white">{t('settings.notifications')}</Label>
                      <p className="text-gray-500 text-sm">Enable desktop notifications</p>
                    </div>
                    <Switch
                      checked={userSettings.notifications_enabled}
                      onCheckedChange={(checked) => setUserSettings({ ...userSettings, notifications_enabled: checked })}
                      data-testid="notifications-switch"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-white/5">
                <Button 
                  onClick={handleSaveUserSettings} 
                  className="btn-primary"
                  disabled={saving}
                  data-testid="save-user-settings-btn"
                >
                  {saving ? t('common.loading') : t('settings.save')}
                </Button>
              </div>
            </motion.div>
          </TabsContent>

          {/* AI Settings (Admin only) */}
          {user?.role === 'admin' && (
            <TabsContent value="ai">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#121212] border border-white/5 rounded-xl p-6 space-y-6"
              >
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">{t('settings.ai')}</h3>
                  
                  <div className="space-y-4">
                    {/* AI Provider */}
                    <div>
                      <Label className="text-white">{t('setup.aiProvider')}</Label>
                      <p className="text-gray-500 text-sm mb-2">Choose how AI features work</p>
                      <Select
                        value={systemSettings.ai_provider}
                        onValueChange={(value) => setSystemSettings({ ...systemSettings, ai_provider: value })}
                      >
                        <SelectTrigger className="bg-black/30 border-white/10 text-white" data-testid="ai-provider-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[#1A1A1A] border-white/10">
                          <SelectItem value="disabled">{t('setup.aiDisabled')}</SelectItem>
                          <SelectItem value="openai">{t('setup.aiOpenai')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* OpenAI API Key */}
                    {systemSettings.ai_provider === 'openai' && (
                      <div>
                        <Label className="text-white">{t('setup.apiKey')}</Label>
                        <Input
                          type="password"
                          value={systemSettings.openai_api_key}
                          onChange={(e) => setSystemSettings({ ...systemSettings, openai_api_key: e.target.value })}
                          className="mt-1 bg-black/30 border-white/10 text-white"
                          placeholder={t('setup.apiKeyPlaceholder')}
                          data-testid="openai-api-key-input"
                        />
                        {systemSettings.openai_api_key === '***configured***' && (
                          <p className="text-green-400 text-sm mt-1 flex items-center gap-1">
                            <Check className="w-4 h-4" /> API key is configured
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5">
                  <Button 
                    onClick={handleSaveSystemSettings} 
                    className="btn-primary"
                    disabled={saving}
                    data-testid="save-ai-settings-btn"
                  >
                    {saving ? t('common.loading') : t('settings.save')}
                  </Button>
                </div>
              </motion.div>
            </TabsContent>
          )}

          {/* Privacy Settings (Admin only) */}
          {user?.role === 'admin' && (
            <TabsContent value="privacy">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#121212] border border-white/5 rounded-xl p-6 space-y-6"
              >
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">{t('settings.privacy')}</h3>
                  
                  <div className="space-y-4">
                    {/* Internet Access */}
                    <div>
                      <Label className="text-white">{t('setup.internetAccess')}</Label>
                      <p className="text-gray-500 text-sm mb-2">Control external connections</p>
                      
                      <div className="grid grid-cols-1 gap-3 mt-2">
                        {[
                          { id: 'denied', label: t('setup.internetDenied'), icon: Shield, color: 'text-green-400' },
                          { id: 'allowed', label: t('setup.internetAllowed'), icon: Globe, color: 'text-amber-400' }
                        ].map((option) => {
                          const Icon = option.icon;
                          return (
                            <button
                              key={option.id}
                              onClick={() => setSystemSettings({ ...systemSettings, internet_access: option.id })}
                              className={`
                                p-4 rounded-lg border transition-all text-left flex items-center gap-3
                                ${systemSettings.internet_access === option.id 
                                  ? 'border-white/30 bg-white/5' 
                                  : 'border-white/10 hover:border-white/20'}
                              `}
                              data-testid={`privacy-internet-${option.id}-btn`}
                            >
                              <Icon className={`w-5 h-5 ${option.color}`} />
                              <span className="text-white font-medium">{option.label}</span>
                              {systemSettings.internet_access === option.id && (
                                <Check className="w-4 h-4 text-white ml-auto" />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {systemSettings.internet_access === 'denied' && (
                      <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                        <p className="text-green-300 text-sm flex items-center gap-2">
                          <Shield className="w-4 h-4" />
                          {t('setup.privacyNote')}
                        </p>
                      </div>
                    )}

                    {systemSettings.internet_access === 'allowed' && systemSettings.ai_provider === 'openai' && (
                      <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                        <p className="text-amber-300 text-sm flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4" />
                          External AI is enabled. Data will be sent to OpenAI servers.
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5">
                  <Button 
                    onClick={handleSaveSystemSettings} 
                    className="btn-primary"
                    disabled={saving}
                    data-testid="save-privacy-settings-btn"
                  >
                    {saving ? t('common.loading') : t('settings.save')}
                  </Button>
                </div>
              </motion.div>
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}
