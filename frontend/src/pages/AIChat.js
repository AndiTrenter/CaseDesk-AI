import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bot, Send, User, Sparkles, AlertCircle, Download, FileText, X, Brain, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { aiAPI, settingsAPI, documentsAPI, casesAPI } from '../lib/api';
import { toast } from 'sonner';

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

  useEffect(() => {
    checkAIStatus();
    setSessionId(`session-${Date.now()}`);
    loadContext();
    loadProfile();
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

  const handleDeleteFact = async (index) => {
    try {
      await aiAPI.deleteProfileFact(index);
      toast.success('Fakt entfernt');
      loadProfile();
    } catch (error) {
      toast.error('Fehler beim Entfernen');
    }
  };

  const handleClearProfile = async () => {
    if (!window.confirm('Gesamtes KI-Gedächtnis wirklich löschen?')) return;
    try {
      await aiAPI.clearProfile();
      setProfile(null);
      toast.success('KI-Gedächtnis gelöscht');
    } catch (error) {
      toast.error('Fehler beim Löschen');
    }
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

    try {
      const response = await aiAPI.chat(userMessage, sessionId, caseId, documentId);
      
      if (response.data.success) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.response,
          referencedDocuments: response.data.referenced_documents || []
        }]);
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
    // Refresh profile after each message (new facts may have been extracted)
    setTimeout(() => loadProfile(), 3000);
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
              {aiEnabled ? 'Stellen Sie Fragen zu Ihren Dokumenten und Fällen' : t('ai.disabled')}
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
                className="text-red-400 hover:bg-red-500/10 text-xs"
                data-testid="clear-ai-memory-btn"
              >
                <Trash2 className="w-3 h-3 mr-1" /> Alles löschen
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
                      : 'Starten Sie ein Gespräch'}
                  </h3>
                  <p className="text-gray-500 max-w-sm">
                    {contextInfo
                      ? `Die KI hat den vollständigen Inhalt von "${contextInfo.type === 'document' ? (contextInfo.data?.display_name || contextInfo.data?.original_filename) : contextInfo.data?.title}" geladen.`
                      : 'Fragen Sie mich zu Ihren Dokumenten, Fällen, Aufgaben oder lassen Sie mich Antworten entwerfen.'}
                  </p>
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
                    <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-purple-400" />
                    </div>
                  )}
                  
                  <div className={`
                    max-w-[80%] rounded-xl px-4 py-3
                    ${message.role === 'user' 
                      ? 'bg-blue-500/20 text-white' 
                      : message.isError
                        ? 'bg-red-500/10 text-red-300 border border-red-500/20'
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
                  : t('ai.placeholder')
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
    </div>
  );
}
