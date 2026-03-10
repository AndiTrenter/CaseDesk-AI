import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, Globe, Shield, Brain, 
  User, Moon, Sun, Check, AlertTriangle, Mail, Plus, Trash2, Download
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { settingsAPI, mailAPI, exportAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

export default function Settings() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [systemSettings, setSystemSettings] = useState({
    ai_provider: 'ollama',
    openai_api_key: '',
    internet_access: 'denied',
    default_language: 'de'
  });
  
  const [userSettings, setUserSettings] = useState({
    language: 'de',
    theme: 'dark',
    notifications_enabled: true
  });
  
  const [mailAccounts, setMailAccounts] = useState([]);
  const [mailDialogOpen, setMailDialogOpen] = useState(false);
  const [newMailAccount, setNewMailAccount] = useState({
    email: '',
    display_name: '',
    imap_server: '',
    imap_port: 993,
    password: ''
  });

  useEffect(() => {
    loadSettings();
    loadMailAccounts();
  }, []);
  
  const loadMailAccounts = async () => {
    try {
      const res = await mailAPI.listAccounts();
      setMailAccounts(res.data);
    } catch (error) {
      console.error('Failed to load mail accounts:', error);
    }
  };

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
  
  const handleAddMailAccount = async () => {
    try {
      await mailAPI.createAccount(newMailAccount);
      toast.success('E-Mail-Konto hinzugefügt');
      setMailDialogOpen(false);
      setNewMailAccount({ email: '', display_name: '', imap_server: '', imap_port: 993, password: '' });
      loadMailAccounts();
    } catch (error) {
      toast.error('Fehler beim Hinzufügen des E-Mail-Kontos');
    }
  };
  
  const handleDeleteMailAccount = async (id) => {
    try {
      await mailAPI.deleteAccount(id);
      toast.success('E-Mail-Konto gelöscht');
      loadMailAccounts();
    } catch (error) {
      toast.error('Fehler beim Löschen');
    }
  };
  
  const handleExportData = async () => {
    try {
      toast.info('Daten werden exportiert...');
      const response = await exportAPI.all();
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `casedesk-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success('Export erfolgreich');
    } catch (error) {
      toast.error('Export fehlgeschlagen');
    }
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
          <TabsList className="bg-white/5 border border-white/10 flex-wrap">
            <TabsTrigger value="user" className="data-[state=active]:bg-white/10">
              <User className="w-4 h-4 mr-2" />
              {t('settings.user')}
            </TabsTrigger>
            <TabsTrigger value="email" className="data-[state=active]:bg-white/10">
              <Mail className="w-4 h-4 mr-2" />
              E-Mail
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
            <TabsTrigger value="export" className="data-[state=active]:bg-white/10">
              <Download className="w-4 h-4 mr-2" />
              Export
            </TabsTrigger>
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
                      <p className="text-gray-500 text-sm mb-2">Wählen Sie den KI-Anbieter</p>
                      
                      <div className="grid grid-cols-1 gap-3 mt-2">
                        {[
                          { id: 'ollama', label: 'Ollama (Lokal)', desc: 'Komplett lokal, kein Internet erforderlich', recommended: true },
                          { id: 'openai', label: t('setup.aiOpenai'), desc: 'Benötigt API-Key und Internetzugriff' },
                          { id: 'disabled', label: t('setup.aiDisabled'), desc: 'KI-Funktionen deaktiviert' }
                        ].map((option) => (
                          <button
                            key={option.id}
                            onClick={() => setSystemSettings({ ...systemSettings, ai_provider: option.id })}
                            className={`
                              p-4 rounded-lg border transition-all text-left relative
                              ${systemSettings.ai_provider === option.id 
                                ? 'border-white/30 bg-white/5' 
                                : 'border-white/10 hover:border-white/20'}
                            `}
                            data-testid={`ai-setting-${option.id}-btn`}
                          >
                            {option.recommended && (
                              <span className="absolute top-2 right-2 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
                                Empfohlen
                              </span>
                            )}
                            <span className="text-white font-medium block">{option.label}</span>
                            <span className="text-gray-500 text-sm">{option.desc}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Ollama Info */}
                    {systemSettings.ai_provider === 'ollama' && (
                      <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                        <p className="text-green-300 text-sm">
                          Ollama läuft lokal auf Ihrem Server. Keine Daten verlassen Ihr System.
                        </p>
                      </div>
                    )}

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

          {/* Email Settings */}
          <TabsContent value="email">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6 space-y-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">E-Mail-Konten</h3>
                  <p className="text-gray-500 text-sm">IMAP-Konten für E-Mail-Abruf konfigurieren</p>
                </div>
                <Button 
                  onClick={() => setMailDialogOpen(true)}
                  className="btn-primary flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" /> Konto hinzufügen
                </Button>
              </div>
              
              {mailAccounts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Mail className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Keine E-Mail-Konten konfiguriert</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {mailAccounts.map(account => (
                    <div 
                      key={account.id}
                      className="flex items-center justify-between p-4 bg-white/5 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                          <Mail className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium">{account.display_name}</p>
                          <p className="text-gray-500 text-sm">{account.email}</p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteMailAccount(account.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </TabsContent>

          {/* Export Settings */}
          <TabsContent value="export">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6 space-y-6"
            >
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Daten exportieren</h3>
                <p className="text-gray-500 text-sm">
                  Exportieren Sie alle Ihre Daten als JSON-Datei für Backup oder Migration.
                </p>
              </div>
              
              <div className="p-4 bg-white/5 rounded-lg">
                <h4 className="text-white font-medium mb-2">Vollständiger Export</h4>
                <p className="text-gray-400 text-sm mb-4">
                  Enthält: Fälle, Dokumente (ohne Dateien), Aufgaben, Termine, E-Mails, Entwürfe
                </p>
                <Button 
                  onClick={handleExportData}
                  className="btn-primary flex items-center gap-2"
                >
                  <Download className="w-4 h-4" /> Alle Daten exportieren
                </Button>
              </div>
              
              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-amber-300 text-sm">
                  Hinweis: Der Export enthält keine Dateien (PDFs, Bilder). Diese müssen separat gesichert werden.
                </p>
              </div>
            </motion.div>
          </TabsContent>
        </Tabs>
      </div>
      
      {/* Add Mail Account Dialog */}
      <Dialog open={mailDialogOpen} onOpenChange={setMailDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>E-Mail-Konto hinzufügen</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-gray-300">E-Mail-Adresse</Label>
              <Input
                type="email"
                value={newMailAccount.email}
                onChange={(e) => setNewMailAccount({ ...newMailAccount, email: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="ihre@email.de"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Anzeigename</Label>
              <Input
                value={newMailAccount.display_name}
                onChange={(e) => setNewMailAccount({ ...newMailAccount, display_name: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="Geschäftlich"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">IMAP-Server</Label>
              <Input
                value={newMailAccount.imap_server}
                onChange={(e) => setNewMailAccount({ ...newMailAccount, imap_server: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="imap.example.com"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">IMAP-Port</Label>
              <Input
                type="number"
                value={newMailAccount.imap_port}
                onChange={(e) => setNewMailAccount({ ...newMailAccount, imap_port: parseInt(e.target.value) })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="993"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Passwort</Label>
              <Input
                type="password"
                value={newMailAccount.password}
                onChange={(e) => setNewMailAccount({ ...newMailAccount, password: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="••••••••"
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setMailDialogOpen(false)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button onClick={handleAddMailAccount} className="btn-primary">
                Hinzufügen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
