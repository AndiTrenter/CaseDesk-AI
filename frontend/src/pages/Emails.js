import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Mail, RefreshCw, Trash2, MoreVertical, Paperclip,
  Calendar, User, AlertCircle, Link, FileText, Download,
  Loader2, CheckCircle, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
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
import { mailAPI, casesAPI } from '../lib/api';
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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [emailsRes, accountsRes, casesRes] = await Promise.all([
        api.get('/emails'),
        mailAPI.listAccounts(),
        casesAPI.list()
      ]);
      setEmails(emailsRes.data);
      setMailAccounts(accountsRes.data);
      setCases(casesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
    setLoading(false);
  };

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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('nav.emails')}</h1>
          <p className="text-gray-400 text-sm">{emails.length} E-Mails</p>
        </div>
        
        <div className="flex items-center gap-3">
          {mailAccounts.length > 0 && (
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
          )}
        </div>
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
      ) : emails.length === 0 ? (
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
          {emails.map((email, index) => (
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
    </div>
  );
}
