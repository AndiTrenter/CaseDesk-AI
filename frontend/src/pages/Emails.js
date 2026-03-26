import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Mail, RefreshCw, Trash2, MoreVertical, Paperclip,
  Calendar, User, AlertCircle, Link, FileText, Download,
  Loader2, CheckCircle, ExternalLink, Plus, Send, Sparkles, X, Search,
  Inbox, SendHorizontal, File, Reply
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { mailAPI, casesAPI, aiAPI } from '../lib/api';
import { toast } from 'sonner';
import api from '../lib/api';

export default function Emails() {
  const { t } = useTranslation();
  const [emails, setEmails] = useState([]);
  const [mailAccounts, setMailAccounts] = useState([]);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [emailToLink, setEmailToLink] = useState(null);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [processing, setProcessing] = useState({});
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  
  // Tab state (inbox vs sent)
  const [activeTab, setActiveTab] = useState('inbox');
  
  // Compose email state
  const [composeOpen, setComposeOpen] = useState(false);
  const [composing, setComposing] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [composeData, setComposeData] = useState({
    to: '',
    subject: '',
    body: '',
    account_id: '',
    attachments: [],
    context_type: null, // 'email' or 'document'
    context_id: null
  });
  const [aiPrompt, setAiPrompt] = useState('');
  const [contextDocument, setContextDocument] = useState(null);
  const [contextEmail, setContextEmail] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showContextPicker, setShowContextPicker] = useState(false);
  const attachmentInputRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [emailsRes, accountsRes, casesRes, docsRes] = await Promise.all([
        api.get('/emails'),
        mailAPI.listAccounts(),
        casesAPI.list(),
        api.get('/documents')
      ]);
      setEmails(emailsRes.data);
      setMailAccounts(accountsRes.data);
      setCases(casesRes.data);
      setDocuments(docsRes.data || []);
      
      // Set default account for compose
      if (accountsRes.data.length > 0 && !composeData.account_id) {
        setComposeData(prev => ({ ...prev, account_id: accountsRes.data[0].id }));
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
    setLoading(false);
  };

  // Filter emails by tab
  const inboxEmails = emails.filter(e => !e.is_sent);
  const sentEmails = emails.filter(e => e.is_sent);
  
  // Get emails for current tab
  const getTabEmails = () => {
    const base = activeTab === 'sent' ? sentEmails : inboxEmails;
    return searchResults !== null ? searchResults : base;
  };

  // Send composed email
  const handleSendEmail = async () => {
    if (!composeData.to || !composeData.subject || !composeData.body) {
      toast.error('Bitte alle Felder ausfüllen');
      return;
    }
    if (!composeData.account_id) {
      toast.error('Bitte ein E-Mail-Konto auswählen');
      return;
    }
    
    setComposing(true);
    try {
      // Create FormData for attachments
      const formData = new FormData();
      formData.append('account_id', composeData.account_id);
      formData.append('to', composeData.to);
      formData.append('subject', composeData.subject);
      formData.append('body', composeData.body);
      
      // Add attachments
      if (composeData.attachments && composeData.attachments.length > 0) {
        composeData.attachments.forEach((file, index) => {
          formData.append(`attachment_${index}`, file);
        });
      }
      
      const response = await api.post('/emails/send', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.success) {
        toast.success('E-Mail erfolgreich gesendet!');
        setComposeOpen(false);
        resetComposeData();
        loadData();
      } else {
        toast.error(response.data.error || 'Senden fehlgeschlagen');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'E-Mail konnte nicht gesendet werden');
    }
    setComposing(false);
  };
  
  // Reset compose data
  const resetComposeData = () => {
    setComposeData({ 
      to: '', 
      subject: '', 
      body: '', 
      account_id: mailAccounts[0]?.id || '',
      attachments: [],
      context_type: null,
      context_id: null
    });
    setAiPrompt('');
    setContextDocument(null);
    setContextEmail(null);
  };
  
  // Add attachment
  const handleAddAttachment = (e) => {
    const files = Array.from(e.target.files || []);
    setComposeData(prev => ({
      ...prev,
      attachments: [...prev.attachments, ...files]
    }));
    if (attachmentInputRef.current) {
      attachmentInputRef.current.value = '';
    }
  };
  
  // Remove attachment
  const handleRemoveAttachment = (index) => {
    setComposeData(prev => ({
      ...prev,
      attachments: prev.attachments.filter((_, i) => i !== index)
    }));
  };
  
  // Set context for AI generation
  const setEmailContext = (email) => {
    setContextEmail(email);
    setContextDocument(null);
    setComposeData(prev => ({
      ...prev,
      context_type: 'email',
      context_id: email.id
    }));
    setShowContextPicker(false);
  };
  
  const setDocumentContext = (doc) => {
    setContextDocument(doc);
    setContextEmail(null);
    setComposeData(prev => ({
      ...prev,
      context_type: 'document',
      context_id: doc.id
    }));
    setShowContextPicker(false);
  };
  
  const clearContext = () => {
    setContextEmail(null);
    setContextDocument(null);
    setComposeData(prev => ({
      ...prev,
      context_type: null,
      context_id: null
    }));
  };

  // Generate email with AI (with context support)
  const handleAIGenerate = async () => {
    if (!aiPrompt.trim()) {
      toast.error('Bitte beschreiben Sie, was die E-Mail enthalten soll');
      return;
    }
    
    setAiGenerating(true);
    try {
      const requestData = {
        prompt: aiPrompt,
        context: {
          recipient: composeData.to,
          subject: composeData.subject
        }
      };
      
      // Add document or email context
      if (contextDocument) {
        requestData.document_id = contextDocument.id;
        requestData.context.document_name = contextDocument.display_name || contextDocument.original_filename;
        requestData.context.document_summary = contextDocument.ai_summary;
      }
      if (contextEmail) {
        requestData.email_id = contextEmail.id;
        requestData.context.email_subject = contextEmail.subject;
        requestData.context.email_from = contextEmail.from_name || contextEmail.from_address;
        requestData.context.email_content = contextEmail.body_text?.substring(0, 2000);
      }
      
      const response = await api.post('/ai/generate-email', requestData);
      
      if (response.data.success) {
        setComposeData(prev => ({
          ...prev,
          subject: response.data.subject || prev.subject,
          body: response.data.body || prev.body
        }));
        setAiPrompt('');
        toast.success('E-Mail wurde generiert!');
      } else {
        toast.error(response.data.error || 'KI-Generierung fehlgeschlagen');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'KI-Generierung nicht verfügbar';
      toast.error(errorMsg);
      console.error('AI generation error:', error);
    }
    setAiGenerating(false);
  };

  // Reply to email
  const handleReply = (email) => {
    setComposeData({
      to: email.from_address,
      subject: email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`,
      body: `\n\n---\nAm ${new Date(email.date).toLocaleString('de-DE')} schrieb ${email.from_name || email.from_address}:\n\n${email.body_text || ''}`,
      account_id: email.account_id || mailAccounts[0]?.id || ''
    });
    setSelectedEmail(null);
    setComposeOpen(true);
  };

  // Search emails with AI
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    
    setSearching(true);
    try {
      const response = await api.post('/emails/search', { query: searchQuery });
      if (response.data.success) {
        setSearchResults(response.data.results);
        if (response.data.results.length === 0) {
          toast.info('Keine E-Mails gefunden');
        }
      }
    } catch (error) {
      // Fallback: client-side search
      const query = searchQuery.toLowerCase();
      const filtered = emails.filter(email => 
        email.subject?.toLowerCase().includes(query) ||
        email.from_address?.toLowerCase().includes(query) ||
        email.from_name?.toLowerCase().includes(query) ||
        email.body_text?.toLowerCase().includes(query) ||
        email.ai_summary?.toLowerCase().includes(query)
      );
      setSearchResults(filtered);
    }
    setSearching(false);
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  // Get displayed emails (search results or all)
  const displayedEmails = searchResults !== null ? searchResults : emails;

  const handleFetchEmails = async (accountId) => {
    setFetching(true);
    try {
      toast.info('E-Mails werden abgerufen...', { duration: 30000, id: 'fetch-emails' });
      const response = await api.post(`/emails/fetch/${accountId}`);
      
      if (response.data.success) {
        toast.success(
          `${response.data.fetched_count} neue E-Mail(s) abgerufen`,
          { id: 'fetch-emails' }
        );
        loadData();
      } else {
        toast.error(response.data.error || 'Abruf fehlgeschlagen', { id: 'fetch-emails' });
      }
    } catch (error) {
      toast.error('E-Mail-Abruf fehlgeschlagen', { id: 'fetch-emails' });
    }
    setFetching(false);
  };

  const handleProcessEmail = async (emailId) => {
    setProcessing(prev => ({ ...prev, [emailId]: true }));
    try {
      const response = await api.post(`/emails/${emailId}/process`);
      if (response.data.success) {
        toast.success('E-Mail analysiert');
        loadData();
      } else {
        toast.error(response.data.error || 'Analyse fehlgeschlagen');
      }
    } catch (error) {
      toast.error('Analyse fehlgeschlagen');
    }
    setProcessing(prev => ({ ...prev, [emailId]: false }));
  };

  const handleLinkToCase = async () => {
    if (!emailToLink || !selectedCaseId) return;
    
    try {
      const formData = new FormData();
      formData.append('case_id', selectedCaseId);
      
      const response = await api.post(`/emails/${emailToLink.id}/link`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.success) {
        toast.success('E-Mail mit Fall verknüpft');
        setLinkDialogOpen(false);
        setEmailToLink(null);
        setSelectedCaseId('');
        loadData();
      }
    } catch (error) {
      toast.error('Verknüpfung fehlgeschlagen');
    }
  };

  const handleImportAttachment = async (emailId, attachmentId) => {
    try {
      const response = await api.post(`/emails/${emailId}/import-attachment/${attachmentId}`);
      if (response.data.success) {
        toast.success('Anhang als Dokument importiert');
      }
    } catch (error) {
      toast.error('Import fehlgeschlagen');
    }
  };

  const handleDeleteEmail = async (emailId) => {
    try {
      await api.delete(`/emails/${emailId}`);
      toast.success('E-Mail gelöscht');
      setSelectedEmail(null);
      loadData();
    } catch (error) {
      toast.error('Löschen fehlgeschlagen');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="page-container" data-testid="emails-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('nav.emails')}</h1>
          <p className="text-gray-400 text-sm">
            {activeTab === 'inbox' ? `${inboxEmails.length} empfangen` : `${sentEmails.length} gesendet`}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {mailAccounts.length > 0 && (
            <>
              <Button 
                onClick={() => setComposeOpen(true)}
                className="bg-green-600 hover:bg-green-700 text-white flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Neue E-Mail
              </Button>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    className="btn-primary flex items-center gap-2"
                    disabled={fetching}
                    data-testid="fetch-emails-btn"
                  >
                    {fetching ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4" />
                    )}
                    E-Mails abrufen
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                  {mailAccounts.map(account => (
                    <DropdownMenuItem
                      key={account.id}
                      onClick={() => handleFetchEmails(account.id)}
                      className="text-gray-300 focus:bg-white/10"
                    >
                      <Mail className="w-4 h-4 mr-2" />
                      {account.display_name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            </>
          )}
        </div>
      </div>

      {/* Tabs: Inbox / Sent */}
      <div className="flex gap-1 mb-6 bg-white/5 p-1 rounded-lg w-fit">
        <button
          onClick={() => { setActiveTab('inbox'); clearSearch(); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'inbox' 
              ? 'bg-blue-500 text-white' 
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Inbox className="w-4 h-4" />
          Posteingang
          {inboxEmails.length > 0 && (
            <span className={`px-1.5 py-0.5 rounded text-xs ${
              activeTab === 'inbox' ? 'bg-blue-600' : 'bg-white/10'
            }`}>
              {inboxEmails.length}
            </span>
          )}
        </button>
        <button
          onClick={() => { setActiveTab('sent'); clearSearch(); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'sent' 
              ? 'bg-green-500 text-white' 
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <SendHorizontal className="w-4 h-4" />
          Gesendet
          {sentEmails.length > 0 && (
            <span className={`px-1.5 py-0.5 rounded text-xs ${
              activeTab === 'sent' ? 'bg-green-600' : 'bg-white/10'
            }`}>
              {sentEmails.length}
            </span>
          )}
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Suche nach Absender, Betreff, Inhalt..."
              className="pl-10 bg-black/30 border-white/10 text-white"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <Button 
            onClick={handleSearch}
            disabled={searching}
            className="btn-primary"
          >
            {searching ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
          </Button>
        </div>
        {searchResults !== null && (
          <p className="text-sm text-gray-400 mt-2">
            {searchResults.length} Ergebnis(se) für "{searchQuery}"
            <button onClick={clearSearch} className="ml-2 text-blue-400 hover:underline">
              Filter zurücksetzen
            </button>
          </p>
        )}
      </div>

      {/* No Mail Accounts Info */}
      {mailAccounts.length === 0 && !loading && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5" />
            <div>
              <h3 className="text-amber-400 font-medium">Kein E-Mail-Konto konfiguriert</h3>
              <p className="text-amber-300/70 text-sm mt-1">
                Fügen Sie ein E-Mail-Konto unter Einstellungen → E-Mail hinzu, um E-Mails abzurufen.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Email List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : getTabEmails().length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Mail className="w-8 h-8 text-gray-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">Keine E-Mails</h3>
          <p className="text-gray-500">
            {mailAccounts.length > 0 
              ? 'Klicken Sie auf "E-Mails abrufen" um neue E-Mails zu laden'
              : 'Konfigurieren Sie zuerst ein E-Mail-Konto'
            }
          </p>
        </motion.div>
      ) : (
        <div className="space-y-3">
          {getTabEmails().map((email, index) => (
            <motion.div
              key={email.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              className={`bg-[#121212] border rounded-xl p-4 hover:border-white/10 transition-colors group cursor-pointer ${
                email.is_read ? 'border-white/5' : 'border-blue-500/30 bg-blue-500/5'
              }`}
              onClick={() => setSelectedEmail(email)}
              data-testid={`email-item-${index}`}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  email.is_read ? 'bg-white/5' : 'bg-blue-500/20'
                }`}>
                  <Mail className={`w-5 h-5 ${email.is_read ? 'text-gray-400' : 'text-blue-400'}`} />
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <h3 className={`font-medium truncate ${email.is_read ? 'text-gray-300' : 'text-white'}`}>
                        {email.subject || '(Kein Betreff)'}
                      </h3>
                      <p className="text-gray-500 text-sm truncate">{email.sender}</p>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {email.is_processed && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded border border-green-500/20">
                          <CheckCircle className="w-3 h-3" /> Analysiert
                        </span>
                      )}
                      {email.attachments?.length > 0 && (
                        <span className="flex items-center gap-1 px-2 py-0.5 bg-white/5 text-gray-400 text-xs rounded">
                          <Paperclip className="w-3 h-3" /> {email.attachments.length}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Summary */}
                  {email.ai_summary && (
                    <p className="text-gray-400 text-sm mt-1 line-clamp-1">{email.ai_summary}</p>
                  )}
                  
                  {/* Meta */}
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> {formatDate(email.received_at)}
                    </span>
                    {email.case_id && (
                      <span className="flex items-center gap-1 text-blue-400">
                        <Link className="w-3 h-3" /> Verknüpft
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Actions */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <MoreVertical className="w-4 h-4 text-gray-400" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                    <DropdownMenuItem 
                      onClick={(e) => { e.stopPropagation(); handleProcessEmail(email.id); }}
                      disabled={processing[email.id]}
                      className="text-gray-300 focus:bg-white/10"
                    >
                      {processing[email.id] ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      KI-Analyse
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={(e) => { 
                        e.stopPropagation(); 
                        setEmailToLink(email); 
                        setLinkDialogOpen(true); 
                      }}
                      className="text-gray-300 focus:bg-white/10"
                    >
                      <Link className="w-4 h-4 mr-2" /> Mit Fall verknüpfen
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={(e) => { e.stopPropagation(); handleDeleteEmail(email.id); }}
                      className="text-red-400 focus:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4 mr-2" /> Löschen
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Email Detail Dialog */}
      <Dialog open={!!selectedEmail} onOpenChange={() => setSelectedEmail(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="pr-8">{selectedEmail?.subject || '(Kein Betreff)'}</DialogTitle>
          </DialogHeader>
          
          {selectedEmail && (
            <div className="space-y-4">
              {/* Header */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-lg">
                <div>
                  <label className="text-gray-500 text-xs">Von</label>
                  <p className="text-white text-sm">{selectedEmail.sender}</p>
                </div>
                <div>
                  <label className="text-gray-500 text-xs">Datum</label>
                  <p className="text-white text-sm">{formatDate(selectedEmail.received_at)}</p>
                </div>
                {selectedEmail.recipients?.length > 0 && (
                  <div className="col-span-2">
                    <label className="text-gray-500 text-xs">An</label>
                    <p className="text-white text-sm">{selectedEmail.recipients.join(', ')}</p>
                  </div>
                )}
              </div>
              
              {/* AI Summary */}
              {selectedEmail.ai_summary && (
                <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                  <label className="text-purple-400 text-xs font-medium">KI-Zusammenfassung</label>
                  <p className="text-white text-sm mt-1">{selectedEmail.ai_summary}</p>
                </div>
              )}
              
              {/* Deadlines */}
              {selectedEmail.detected_deadlines?.length > 0 && (
                <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                  <label className="text-amber-400 text-xs font-medium flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> Erkannte Fristen
                  </label>
                  <p className="text-white text-sm mt-1">{selectedEmail.detected_deadlines.join(', ')}</p>
                </div>
              )}
              
              {/* Attachments */}
              {selectedEmail.attachments?.length > 0 && (
                <div>
                  <label className="text-gray-400 text-sm font-medium">Anhänge</label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {selectedEmail.attachments.map((att) => (
                      <div 
                        key={att.id}
                        className="flex items-center gap-2 p-3 bg-white/5 rounded-lg group"
                      >
                        <FileText className="w-4 h-4 text-gray-400" />
                        <span className="flex-1 text-sm text-white truncate">{att.filename}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleImportAttachment(selectedEmail.id, att.id)}
                          className="opacity-0 group-hover:opacity-100 h-6 px-2"
                        >
                          <Download className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Body */}
              <div>
                <label className="text-gray-400 text-sm font-medium">Inhalt</label>
                <div className="mt-2 p-4 bg-black/30 rounded-lg max-h-60 overflow-y-auto">
                  <pre className="text-gray-300 text-sm whitespace-pre-wrap font-sans">
                    {selectedEmail.body_text || '(Kein Textinhalt)'}
                  </pre>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-white/5">
                <Button
                  onClick={() => {
                    setEmailToLink(selectedEmail);
                    setLinkDialogOpen(true);
                  }}
                  className="btn-secondary"
                >
                  <Link className="w-4 h-4 mr-2" /> Mit Fall verknüpfen
                </Button>
                <Button
                  onClick={() => handleProcessEmail(selectedEmail.id)}
                  disabled={processing[selectedEmail.id]}
                  className="btn-secondary"
                >
                  {processing[selectedEmail.id] ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4 mr-2" />
                  )}
                  KI-Analyse
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Link to Case Dialog */}
      <Dialog open={linkDialogOpen} onOpenChange={setLinkDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>E-Mail mit Fall verknüpfen</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">
              Wählen Sie einen Fall aus, mit dem diese E-Mail verknüpft werden soll.
            </p>
            
            <Select value={selectedCaseId} onValueChange={setSelectedCaseId}>
              <SelectTrigger className="bg-black/30 border-white/10 text-white">
                <SelectValue placeholder="Fall auswählen..." />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1A1A] border-white/10">
                {cases.map(c => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setLinkDialogOpen(false)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button 
                onClick={handleLinkToCase} 
                disabled={!selectedCaseId}
                className="btn-primary"
              >
                Verknüpfen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Compose Email Dialog */}
      <Dialog open={composeOpen} onOpenChange={(open) => { setComposeOpen(open); if (!open) resetComposeData(); }}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-green-400" />
              Neue E-Mail verfassen
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Account Selection */}
            <div>
              <Label className="text-gray-300">Von</Label>
              <Select
                value={composeData.account_id}
                onValueChange={(value) => setComposeData({ ...composeData, account_id: value })}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue placeholder="E-Mail-Konto wählen" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  {mailAccounts.map(account => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.display_name} ({account.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* To */}
            <div>
              <Label className="text-gray-300">An</Label>
              <Input
                type="email"
                value={composeData.to}
                onChange={(e) => setComposeData({ ...composeData, to: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="empfaenger@email.de"
              />
            </div>
            
            {/* Subject */}
            <div>
              <Label className="text-gray-300">Betreff</Label>
              <Input
                value={composeData.subject}
                onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="Betreff der E-Mail"
              />
            </div>
            
            {/* Context Selection for AI */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <span className="text-blue-400 font-medium text-sm">Kontext für KI</span>
                </div>
                {(contextEmail || contextDocument) && (
                  <button onClick={clearContext} className="text-xs text-gray-500 hover:text-white">
                    Kontext entfernen
                  </button>
                )}
              </div>
              
              {contextEmail ? (
                <div className="flex items-center gap-2 p-2 bg-black/20 rounded">
                  <Mail className="w-4 h-4 text-blue-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm truncate">{contextEmail.subject}</p>
                    <p className="text-gray-500 text-xs">von {contextEmail.from_name || contextEmail.from_address}</p>
                  </div>
                </div>
              ) : contextDocument ? (
                <div className="flex items-center gap-2 p-2 bg-black/20 rounded">
                  <File className="w-4 h-4 text-green-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm truncate">{contextDocument.display_name || contextDocument.original_filename}</p>
                    <p className="text-gray-500 text-xs">{contextDocument.ai_summary?.substring(0, 50)}...</p>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowContextPicker('email')}
                    className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    E-Mail auswählen
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowContextPicker('document')}
                    className="border-green-500/30 text-green-400 hover:bg-green-500/10"
                  >
                    <File className="w-4 h-4 mr-2" />
                    Dokument auswählen
                  </Button>
                </div>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Wählen Sie eine E-Mail oder ein Dokument als Kontext für die KI-Generierung
              </p>
            </div>
            
            {/* AI Generation */}
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span className="text-purple-400 font-medium text-sm">KI-Assistent</span>
              </div>
              <div className="flex gap-2">
                <Input
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  className="bg-black/30 border-white/10 text-white"
                  placeholder={contextEmail || contextDocument 
                    ? "z.B. 'Antworte höflich und bitte um Fristverlängerung'" 
                    : "z.B. 'Schreibe eine höfliche Anfrage wegen Zahlungsaufschub'"
                  }
                  onKeyDown={(e) => e.key === 'Enter' && handleAIGenerate()}
                />
                <Button 
                  onClick={handleAIGenerate}
                  disabled={aiGenerating || !aiPrompt.trim()}
                  className="bg-purple-600 hover:bg-purple-700 text-white shrink-0"
                >
                  {aiGenerating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {contextEmail || contextDocument 
                  ? "Die KI nutzt den ausgewählten Kontext um eine passende Antwort zu generieren"
                  : "Beschreiben Sie den Inhalt und die KI generiert die E-Mail für Sie"
                }
              </p>
            </div>
            
            {/* Body */}
            <div>
              <Label className="text-gray-300">Nachricht</Label>
              <Textarea
                value={composeData.body}
                onChange={(e) => setComposeData({ ...composeData, body: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white min-h-[200px]"
                placeholder="Ihre Nachricht..."
              />
            </div>
            
            {/* Attachments */}
            <div>
              <Label className="text-gray-300">Anhänge</Label>
              <input
                ref={attachmentInputRef}
                type="file"
                multiple
                onChange={handleAddAttachment}
                className="hidden"
              />
              <div className="mt-2 space-y-2">
                {composeData.attachments.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-white/5 rounded">
                    <Paperclip className="w-4 h-4 text-gray-400" />
                    <span className="text-white text-sm flex-1 truncate">{file.name}</span>
                    <span className="text-gray-500 text-xs">{(file.size / 1024).toFixed(0)} KB</span>
                    <button onClick={() => handleRemoveAttachment(index)} className="text-red-400 hover:text-red-300">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => attachmentInputRef.current?.click()}
                  className="border-white/10 text-gray-400 hover:bg-white/5"
                >
                  <Paperclip className="w-4 h-4 mr-2" />
                  Anhang hinzufügen
                </Button>
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4">
              <Button 
                variant="ghost" 
                onClick={() => { setComposeOpen(false); resetComposeData(); }} 
                className="text-gray-400"
              >
                Abbrechen
              </Button>
              <Button 
                onClick={handleSendEmail}
                disabled={composing || !composeData.to || !composeData.subject || !composeData.body}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {composing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Wird gesendet...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Senden
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Context Picker Dialog */}
      <Dialog open={!!showContextPicker} onOpenChange={() => setShowContextPicker(false)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-lg max-h-[70vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {showContextPicker === 'email' ? 'E-Mail als Kontext wählen' : 'Dokument als Kontext wählen'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-2 max-h-[50vh] overflow-y-auto">
            {showContextPicker === 'email' ? (
              inboxEmails.slice(0, 20).map(email => (
                <button
                  key={email.id}
                  onClick={() => setEmailContext(email)}
                  className="w-full flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-lg text-left transition-colors"
                >
                  <Mail className="w-4 h-4 text-blue-400 mt-1 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{email.subject}</p>
                    <p className="text-gray-500 text-xs">von {email.from_name || email.from_address}</p>
                  </div>
                </button>
              ))
            ) : (
              documents.slice(0, 20).map(doc => (
                <button
                  key={doc.id}
                  onClick={() => setDocumentContext(doc)}
                  className="w-full flex items-start gap-3 p-3 bg-white/5 hover:bg-white/10 rounded-lg text-left transition-colors"
                >
                  <File className="w-4 h-4 text-green-400 mt-1 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{doc.display_name || doc.original_filename}</p>
                    <p className="text-gray-500 text-xs truncate">{doc.ai_summary || 'Keine Zusammenfassung'}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
