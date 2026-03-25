import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, Send, User, Sparkles, AlertCircle, Download, FileText, X, Brain, 
  Trash2, ChevronDown, ChevronUp, Calendar, CheckSquare, Folder, Mail,
  Clock, MapPin, AlertTriangle, Check, Edit, Loader2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { aiAPI, settingsAPI, documentsAPI, casesAPI, mailAPI } from '../lib/api';
import { toast } from 'sonner';

// Action Card Component for previewing detected actions
function ActionPreviewCard({ actionType, actionData, onConfirm, onEdit, onCancel, isExecuting }) {
  const getActionIcon = () => {
    switch (actionType) {
      case 'create_event': return <Calendar className="w-5 h-5 text-blue-400" />;
      case 'create_task': return <CheckSquare className="w-5 h-5 text-green-400" />;
      case 'create_case': return <Folder className="w-5 h-5 text-amber-400" />;
      case 'send_email': return <Mail className="w-5 h-5 text-purple-400" />;
      default: return <Sparkles className="w-5 h-5 text-gray-400" />;
    }
  };

  const getActionTitle = () => {
    switch (actionType) {
      case 'create_event': return 'Termin erstellen';
      case 'create_task': return 'Aufgabe erstellen';
      case 'create_case': return 'Fall anlegen';
      case 'send_email': return 'E-Mail vorbereiten';
      default: return 'Aktion';
    }
  };

  const getActionColor = () => {
    switch (actionType) {
      case 'create_event': return 'border-blue-500/30 bg-blue-500/5';
      case 'create_task': return 'border-green-500/30 bg-green-500/5';
      case 'create_case': return 'border-amber-500/30 bg-amber-500/5';
      case 'send_email': return 'border-purple-500/30 bg-purple-500/5';
      default: return 'border-white/10 bg-white/5';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border p-4 ${getActionColor()}`}
    >
      <div className="flex items-center gap-3 mb-3">
        {getActionIcon()}
        <h4 className="text-white font-medium">{getActionTitle()}</h4>
      </div>

      <div className="space-y-2 text-sm mb-4">
        {actionType === 'create_event' && (
          <>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Titel:</span> {actionData.title}
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <Calendar className="w-4 h-4 text-gray-500" />
              {actionData.date} {!actionData.all_day && `${actionData.start_time} - ${actionData.end_time}`}
              {actionData.all_day && '(Ganztägig)'}
            </div>
            {actionData.location && (
              <div className="flex items-center gap-2 text-gray-300">
                <MapPin className="w-4 h-4 text-gray-500" />
                {actionData.location}
              </div>
            )}
            {actionData.ask_reminder && (
              <div className="flex items-center gap-2 text-amber-300 bg-amber-500/10 px-2 py-1 rounded text-xs">
                <AlertTriangle className="w-3 h-3" />
                Soll ich auch eine Erinnerung erstellen?
              </div>
            )}
          </>
        )}

        {actionType === 'create_task' && (
          <>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Titel:</span> {actionData.title}
            </div>
            {actionData.due_date && (
              <div className="flex items-center gap-2 text-gray-300">
                <Clock className="w-4 h-4 text-gray-500" />
                Fällig: {actionData.due_date}
              </div>
            )}
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Priorität:</span> 
              <span className={`px-2 py-0.5 rounded text-xs ${
                actionData.priority === 'high' || actionData.priority === 'urgent' 
                  ? 'bg-red-500/20 text-red-300' 
                  : actionData.priority === 'medium' 
                    ? 'bg-amber-500/20 text-amber-300'
                    : 'bg-gray-500/20 text-gray-300'
              }`}>
                {actionData.priority}
              </span>
            </div>
          </>
        )}

        {actionType === 'create_case' && (
          <>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Titel:</span> {actionData.title}
            </div>
            {actionData.description && (
              <div className="text-gray-400 text-xs mt-1">{actionData.description}</div>
            )}
            {actionData.reference_number && (
              <div className="flex items-center gap-2 text-gray-300">
                <span className="text-gray-500">Aktenzeichen:</span> {actionData.reference_number}
              </div>
            )}
          </>
        )}

        {actionType === 'send_email' && (
          <>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">An:</span> {actionData.recipient}
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Betreff:</span> {actionData.subject}
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="text-gray-500">Anliegen:</span> {actionData.purpose}
            </div>
            {actionData.draft_content && (
              <div className="mt-2 p-2 bg-black/20 rounded text-gray-300 text-xs max-h-32 overflow-y-auto whitespace-pre-wrap">
                {actionData.draft_content}
              </div>
            )}
            {actionData.suggested_documents?.length > 0 && (
              <div className="mt-2 text-xs text-gray-400">
                <span className="text-gray-500">Empfohlene Anlagen:</span> {actionData.suggested_documents.join(', ')}
              </div>
            )}
          </>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          onClick={onConfirm}
          disabled={isExecuting}
          className="flex-1 bg-white/10 hover:bg-white/20 text-white"
        >
          {isExecuting ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Check className="w-4 h-4 mr-2" />
          )}
          {actionType === 'send_email' ? 'Entwurf erstellen' : 'Bestätigen'}
        </Button>
        <Button
          onClick={onEdit}
          variant="ghost"
          className="text-gray-400 hover:text-white"
        >
          <Edit className="w-4 h-4" />
        </Button>
        <Button
          onClick={onCancel}
          variant="ghost"
          className="text-gray-400 hover:text-red-400"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
}

// Email Send Dialog
function EmailSendDialog({ correspondence, mailAccounts, onSend, onClose, isSending }) {
  const [selectedAccount, setSelectedAccount] = useState('');
  const [recipientEmail, setRecipientEmail] = useState(correspondence?.recipient_email || '');

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-[#1a1a1a] rounded-xl border border-white/10 max-w-lg w-full p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Mail className="w-5 h-5 text-purple-400" />
          E-Mail versenden
        </h3>

        <div className="space-y-4 mb-6">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">E-Mail-Konto</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-white"
            >
              <option value="">Konto auswählen...</option>
              {mailAccounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.display_name} ({acc.email})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-1 block">Empfänger E-Mail</label>
            <Input
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="empfaenger@example.com"
              className="bg-black/30 border-white/10"
            />
          </div>

          <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
            <p className="text-sm text-gray-400 mb-1">Betreff:</p>
            <p className="text-white text-sm">{correspondence?.subject}</p>
          </div>

          {!mailAccounts.some(acc => acc.smtp_server) && (
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-amber-300 text-sm">
              <AlertTriangle className="w-4 h-4 inline mr-2" />
              SMTP ist für Ihre E-Mail-Konten nicht konfiguriert. E-Mail-Versand ist derzeit nicht möglich.
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <Button
            onClick={() => onSend(selectedAccount, recipientEmail)}
            disabled={!selectedAccount || !recipientEmail || isSending}
            className="flex-1 btn-primary"
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            Senden
          </Button>
          <Button onClick={onClose} variant="ghost" className="text-gray-400">
            Abbrechen
          </Button>
        </div>
      </motion.div>
    </div>
  );
}

// Reminder Dialog for Events
function ReminderDialog({ eventData, onConfirm, onSkip }) {
  const [reminderDays, setReminderDays] = useState(1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4"
    >
      <h4 className="text-amber-300 font-medium mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        Erinnerung erstellen?
      </h4>
      <p className="text-gray-400 text-sm mb-3">
        Soll ich eine Erinnerung für "{eventData.title}" am {eventData.date} erstellen?
      </p>
      <div className="flex items-center gap-3 mb-4">
        <Input
          type="number"
          min="1"
          max="30"
          value={reminderDays}
          onChange={(e) => setReminderDays(parseInt(e.target.value) || 1)}
          className="w-20 bg-black/30 border-white/10 text-center"
        />
        <span className="text-gray-400 text-sm">Tag(e) vorher</span>
      </div>
      <div className="flex gap-2">
        <Button onClick={() => onConfirm(reminderDays)} className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-300">
          <Check className="w-4 h-4 mr-2" />
          Ja, erstellen
        </Button>
        <Button onClick={onSkip} variant="ghost" className="text-gray-400">
          Nein, danke
        </Button>
      </div>
    </motion.div>
  );
}

export default function AIChat() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(null);

  // Context from URL params
  const documentId = searchParams.get('document_id');
  const caseId = searchParams.get('case_id');
  const [contextInfo, setContextInfo] = useState(null);

  // AI Memory state
  const [profileOpen, setProfileOpen] = useState(false);
  const [profile, setProfile] = useState(null);

  // Action state
  const [pendingAction, setPendingAction] = useState(null);
  const [isExecutingAction, setIsExecutingAction] = useState(false);
  const [showReminderDialog, setShowReminderDialog] = useState(false);
  const [pendingEventData, setPendingEventData] = useState(null);

  // Email send dialog
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [pendingCorrespondence, setPendingCorrespondence] = useState(null);
  const [mailAccounts, setMailAccounts] = useState([]);
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  useEffect(() => {
    checkAIStatus();
    setSessionId(`session-${Date.now()}`);
    loadContext();
    loadProfile();
    loadMailAccounts();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const checkAIStatus = async () => {
    try {
      const response = await settingsAPI.getSystem();
      setAiEnabled(response.data?.ai_provider !== 'disabled');
    } catch (error) {
      setAiEnabled(false);
    }
  };

  const loadContext = async () => {
    try {
      if (documentId) {
        const response = await documentsAPI.get(documentId);
        setContextInfo({ type: 'document', data: response.data });
      } else if (caseId) {
        const response = await casesAPI.get(caseId);
        setContextInfo({ type: 'case', data: response.data });
      }
    } catch (error) {
      console.error('Failed to load context:', error);
    }
  };

  const loadProfile = async () => {
    try {
      const response = await aiAPI.getProfile();
      if (response.data.success) {
        setProfile(response.data.profile);
      }
    } catch (error) {
      console.error('Failed to load AI profile:', error);
    }
  };

  const loadMailAccounts = async () => {
    try {
      const response = await mailAPI.listAccounts();
      setMailAccounts(response.data || []);
    } catch (error) {
      console.error('Failed to load mail accounts:', error);
    }
  };

  const handleDeleteFact = async (index) => {
    try {
      await aiAPI.deleteProfileFact(index);
      toast.success('Fakt entfernt');
      loadProfile();
    } catch (error) {
      toast.error('Fehler beim Entfernen');
    }
  };

  const handleClearProfile = () => {
    navigate('/ai-knowledge');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const clearContext = () => {
    navigate('/ai');
    setContextInfo(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    setPendingAction(null);

    try {
      const response = await aiAPI.chat(userMessage, sessionId, caseId, documentId);
      
      if (response.data.success) {
        const newMessage = { 
          role: 'assistant', 
          content: response.data.response,
          referencedDocuments: response.data.referenced_documents || []
        };
        
        setMessages(prev => [...prev, newMessage]);

        // Check for action preview
        if (response.data.action_preview) {
          setPendingAction(response.data.action_preview);
        }
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.error || 'Ein Fehler ist aufgetreten',
          isError: true
        }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Verbindungsfehler. Bitte versuchen Sie es erneut.',
        isError: true
      }]);
    }

    setIsLoading(false);
    setTimeout(() => loadProfile(), 3000);
  };

  const handleConfirmAction = async () => {
    if (!pendingAction) return;

    const { action_type, action_data } = pendingAction;

    // For events, check if we need to ask about reminders
    if (action_type === 'create_event' && action_data.ask_reminder && !action_data.create_reminder) {
      setPendingEventData(action_data);
      setShowReminderDialog(true);
      return;
    }

    setIsExecutingAction(true);

    try {
      const response = await aiAPI.executeAction(action_type, action_data);
      
      if (response.data.success) {
        toast.success(response.data.message);
        
        // Add confirmation message
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ ${response.data.message}`,
          isSuccess: true
        }]);

        // For emails, show send dialog
        if (action_type === 'send_email' && response.data.created) {
          setPendingCorrespondence(response.data.created);
          setShowEmailDialog(true);
        }

        setPendingAction(null);
      } else {
        toast.error(response.data.error || 'Aktion fehlgeschlagen');
      }
    } catch (error) {
      console.error('Action execution error:', error);
      toast.error('Fehler bei der Ausführung');
    }

    setIsExecutingAction(false);
  };

  const handleReminderConfirm = async (days) => {
    setShowReminderDialog(false);
    
    const actionData = {
      ...pendingEventData,
      create_reminder: true,
      reminder_days: days
    };

    setIsExecutingAction(true);

    try {
      const response = await aiAPI.executeAction('create_event', actionData);
      
      if (response.data.success) {
        let message = response.data.message;
        if (response.data.reminder_task) {
          message += ` Erinnerung ${days} Tag(e) vorher erstellt.`;
        }
        toast.success(message);
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ ${message}`,
          isSuccess: true
        }]);

        setPendingAction(null);
        setPendingEventData(null);
      } else {
        toast.error(response.data.error || 'Aktion fehlgeschlagen');
      }
    } catch (error) {
      console.error('Action execution error:', error);
      toast.error('Fehler bei der Ausführung');
    }

    setIsExecutingAction(false);
  };

  const handleReminderSkip = async () => {
    setShowReminderDialog(false);
    
    const actionData = {
      ...pendingEventData,
      create_reminder: false
    };

    setIsExecutingAction(true);

    try {
      const response = await aiAPI.executeAction('create_event', actionData);
      
      if (response.data.success) {
        toast.success(response.data.message);
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ ${response.data.message}`,
          isSuccess: true
        }]);

        setPendingAction(null);
        setPendingEventData(null);
      } else {
        toast.error(response.data.error || 'Aktion fehlgeschlagen');
      }
    } catch (error) {
      console.error('Action execution error:', error);
      toast.error('Fehler bei der Ausführung');
    }

    setIsExecutingAction(false);
  };

  const handleSendEmail = async (accountId, recipientEmail) => {
    if (!pendingCorrespondence || !accountId || !recipientEmail) return;

    setIsSendingEmail(true);

    try {
      const response = await aiAPI.sendCorrespondence(pendingCorrespondence.id, accountId, recipientEmail);
      
      if (response.data.success) {
        toast.success('E-Mail erfolgreich gesendet!');
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `📧 E-Mail "${pendingCorrespondence.subject}" wurde an ${recipientEmail} gesendet.`,
          isSuccess: true
        }]);

        setShowEmailDialog(false);
        setPendingCorrespondence(null);
      } else {
        toast.error(response.data.error || 'E-Mail-Versand fehlgeschlagen');
      }
    } catch (error) {
      console.error('Email send error:', error);
      toast.error('Fehler beim E-Mail-Versand');
    }

    setIsSendingEmail(false);
  };

  const handleCancelAction = () => {
    setPendingAction(null);
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Aktion abgebrochen.',
      isInfo: true
    }]);
  };

  const handleEditAction = () => {
    // For now, just cancel and let user reformulate
    setPendingAction(null);
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Bitte formulieren Sie Ihre Anfrage genauer.',
      isInfo: true
    }]);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (aiEnabled === null) {
    return (
      <div className="page-container flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  return (
    <div className="page-container" data-testid="ai-chat-page">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
                <Bot className="w-5 h-5 text-purple-400" />
              </div>
              {t('ai.title')}
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              {aiEnabled ? 'Stellen Sie Fragen oder geben Sie Anweisungen wie "Erstelle einen Termin..." oder "Schreibe eine E-Mail an..."' : t('ai.disabled')}
            </p>
          </div>

          {/* AI Memory Toggle */}
          {profile && profile.facts && profile.facts.length > 0 && (
            <Button
              variant="ghost"
              onClick={() => setProfileOpen(!profileOpen)}
              className="text-purple-400 hover:bg-purple-500/10"
              data-testid="ai-memory-toggle"
            >
              <Brain className="w-4 h-4 mr-2" />
              Gedächtnis ({profile.facts.length})
              {profileOpen ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
            </Button>
          )}
        </div>

        {/* AI Memory Panel */}
        <AnimatePresence>
          {profileOpen && profile && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 bg-purple-500/5 border border-purple-500/20 rounded-xl p-4"
              data-testid="ai-memory-panel"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-purple-400 font-medium flex items-center gap-2">
                  <Brain className="w-4 h-4" /> KI-Gedächtnis
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearProfile}
                  className="text-gray-400 hover:text-purple-300 text-xs"
                  data-testid="manage-ai-memory-btn"
                >
                  Verwalten
                </Button>
              </div>
              {profile.summary && (
                <p className="text-gray-300 text-sm mb-3">{profile.summary}</p>
              )}
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {profile.facts.map((fact, index) => (
                  <div key={index} className="flex items-center justify-between gap-2 px-3 py-1.5 bg-black/20 rounded text-sm group">
                    <span className="text-gray-400 min-w-0">
                      <span className="text-purple-300 font-medium">{fact.key}:</span>{' '}
                      {fact.value}
                    </span>
                    <button
                      onClick={() => handleDeleteFact(index)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 flex-shrink-0"
                      data-testid={`delete-fact-${index}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Context Banner */}
        {contextInfo && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-4 p-3 rounded-xl border flex items-center justify-between ${
              contextInfo.type === 'document'
                ? 'bg-blue-500/10 border-blue-500/20'
                : 'bg-amber-500/10 border-amber-500/20'
            }`}
            data-testid="context-banner"
          >
            <div className="flex items-center gap-3 min-w-0">
              {contextInfo.type === 'document' ? (
                <FileText className="w-5 h-5 text-blue-400 flex-shrink-0" />
              ) : (
                <Sparkles className="w-5 h-5 text-amber-400 flex-shrink-0" />
              )}
              <div className="min-w-0">
                <p className="text-xs text-gray-400">
                  {contextInfo.type === 'document' ? 'Kontext: Dokument' : 'Kontext: Fall'}
                </p>
                <p className="text-white text-sm font-medium truncate">
                  {contextInfo.type === 'document'
                    ? contextInfo.data?.display_name || contextInfo.data?.original_filename
                    : contextInfo.data?.title
                  }
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearContext}
              className="text-gray-400 hover:text-white flex-shrink-0"
              data-testid="clear-context-btn"
            >
              <X className="w-4 h-4" />
            </Button>
          </motion.div>
        )}

        {/* Chat Container */}
        <div className="bg-[#121212] border border-white/5 rounded-xl overflow-hidden flex flex-col" style={{ height: contextInfo ? 'calc(100vh - 340px)' : 'calc(100vh - 280px)' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {!aiEnabled ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-16 h-16 bg-amber-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <AlertCircle className="w-8 h-8 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">{t('ai.disabled')}</h3>
                  <p className="text-gray-500 max-w-sm">{t('ai.enableHint')}</p>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-500/10 rounded-xl flex items-center justify-center mx-auto mb-4 animate-pulse-glow">
                    <Sparkles className="w-8 h-8 text-purple-400" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">
                    {contextInfo
                      ? contextInfo.type === 'document'
                        ? 'Fragen Sie zur Datei'
                        : 'Fragen Sie zum Fall'
                      : 'Was kann ich für Sie tun?'}
                  </h3>
                  <p className="text-gray-500 max-w-sm mb-4">
                    {contextInfo
                      ? `Die KI hat den vollständigen Inhalt von "${contextInfo.type === 'document' ? (contextInfo.data?.display_name || contextInfo.data?.original_filename) : contextInfo.data?.title}" geladen.`
                      : 'Stellen Sie Fragen oder geben Sie Anweisungen.'}
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center text-xs">
                    <span className="px-2 py-1 bg-blue-500/10 text-blue-300 rounded">📅 "Lege einen Termin an..."</span>
                    <span className="px-2 py-1 bg-green-500/10 text-green-300 rounded">✅ "Erstelle eine Aufgabe..."</span>
                    <span className="px-2 py-1 bg-purple-500/10 text-purple-300 rounded">📧 "Schreibe eine E-Mail an..."</span>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}
                >
                  {message.role === 'assistant' && (
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      message.isSuccess ? 'bg-green-500/20' : 
                      message.isError ? 'bg-red-500/20' : 
                      message.isInfo ? 'bg-gray-500/20' : 'bg-purple-500/20'
                    }`}>
                      <Bot className={`w-4 h-4 ${
                        message.isSuccess ? 'text-green-400' : 
                        message.isError ? 'text-red-400' : 
                        message.isInfo ? 'text-gray-400' : 'text-purple-400'
                      }`} />
                    </div>
                  )}
                  
                  <div className={`
                    max-w-[80%] rounded-xl px-4 py-3
                    ${message.role === 'user' 
                      ? 'bg-blue-500/20 text-white' 
                      : message.isError
                        ? 'bg-red-500/10 text-red-300 border border-red-500/20'
                        : message.isSuccess
                          ? 'bg-green-500/10 text-green-300 border border-green-500/20'
                          : message.isInfo
                            ? 'bg-gray-500/10 text-gray-300 border border-gray-500/20'
                            : 'bg-white/5 text-gray-200'}
                  `}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {/* Referenced Documents - Download Links */}
                    {message.referencedDocuments && message.referencedDocuments.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/10">
                        <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                          <FileText className="w-3 h-3" /> Referenzierte Dokumente:
                        </p>
                        <div className="space-y-1">
                          {message.referencedDocuments.map((doc) => (
                            <a
                              key={doc.id}
                              href={`${process.env.REACT_APP_BACKEND_URL}${doc.download_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors py-1 px-2 rounded bg-blue-500/10 hover:bg-blue-500/20"
                              data-testid={`doc-download-${doc.id}`}
                            >
                              <Download className="w-3 h-3 flex-shrink-0" />
                              <span className="truncate">{doc.name}</span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-blue-400" />
                    </div>
                  )}
                </motion.div>
              ))
            )}
            
            {/* Pending Action Preview */}
            {pendingAction && !showReminderDialog && (
              <ActionPreviewCard
                actionType={pendingAction.action_type}
                actionData={pendingAction.action_data}
                onConfirm={handleConfirmAction}
                onEdit={handleEditAction}
                onCancel={handleCancelAction}
                isExecuting={isExecutingAction}
              />
            )}

            {/* Reminder Dialog */}
            {showReminderDialog && pendingEventData && (
              <ReminderDialog
                eventData={pendingEventData}
                onConfirm={handleReminderConfirm}
                onSkip={handleReminderSkip}
              />
            )}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-purple-400" />
                </div>
                <div className="bg-white/5 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-white/5 p-4">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={contextInfo
                  ? `Frage zu "${contextInfo.type === 'document' ? (contextInfo.data?.display_name || '') : (contextInfo.data?.title || '')}"...`
                  : 'Nachricht eingeben oder Anweisung geben...'
                }
                className="flex-1 bg-black/30 border-white/10 text-white resize-none min-h-[50px] max-h-[120px]"
                disabled={!aiEnabled || isLoading}
                rows={1}
                data-testid="ai-chat-input"
              />
              <Button
                type="submit"
                disabled={!aiEnabled || isLoading || !input.trim()}
                className="btn-primary self-end"
                data-testid="ai-chat-send-btn"
              >
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* Email Send Dialog */}
      {showEmailDialog && pendingCorrespondence && (
        <EmailSendDialog
          correspondence={pendingCorrespondence}
          mailAccounts={mailAccounts}
          onSend={handleSendEmail}
          onClose={() => {
            setShowEmailDialog(false);
            setPendingCorrespondence(null);
          }}
          isSending={isSendingEmail}
        />
      )}
    </div>
  );
}
