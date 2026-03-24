import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Bot, Send, User, Sparkles, AlertCircle, Download, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { aiAPI, settingsAPI } from '../lib/api';
import { toast } from 'sonner';

export default function AIChat() {
  const { t } = useTranslation();
  const messagesEndRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(null);

  useEffect(() => {
    checkAIStatus();
    // Generate session ID
    setSessionId(`session-${Date.now()}`);
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await aiAPI.chat(userMessage, sessionId, null);
      
      if (response.data.success) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.response,
          referencedDocuments: response.data.referenced_documents || []
        }]);
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: response.data.error || 'An error occurred',
          isError: true
        }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Failed to get response. Please try again.',
        isError: true
      }]);
    }

    setIsLoading(false);
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
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
              <Bot className="w-5 h-5 text-purple-400" />
            </div>
            {t('ai.title')}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {aiEnabled ? 'Ask questions about your documents and cases' : t('ai.disabled')}
          </p>
        </div>

        {/* Chat Container */}
        <div className="bg-[#121212] border border-white/5 rounded-xl overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 280px)' }}>
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
                  <h3 className="text-lg font-medium text-white mb-2">Start a conversation</h3>
                  <p className="text-gray-500 max-w-sm">
                    Ask me about your documents, cases, tasks, or let me help you draft responses.
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
                placeholder={t('ai.placeholder')}
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
