import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, FileText, Mail, Send, Download, Edit, Trash2,
  Plus, RefreshCw, Loader2, Sparkles, History, CheckCircle,
  AlertCircle, Calendar, User, Paperclip, Eye, X, Save,
  Lightbulb, Clock, Bell, ChevronRight, Brain, Upload, Link, Bot
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { casesAPI, caseResponseAPI, correspondenceAPI, mailAPI, documentUpdateAPI, proactiveAI, documentsAPI } from '../lib/api';
import { toast } from 'sonner';

const STATUS_COLORS = {
  open: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  in_progress: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  waiting: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  closed: 'bg-gray-500/10 text-gray-400 border-gray-500/20'
};

export default function CaseDetail() {
  const { t } = useTranslation();
  const { caseId } = useParams();
  const navigate = useNavigate();
  
  const [caseData, setCaseData] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [correspondence, setCorrespondence] = useState([]);
  const [history, setHistory] = useState([]);
  const [mailAccounts, setMailAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  
  // Proactive AI state
  const [proactiveAnalysis, setProactiveAnalysis] = useState(null);
  const [loadingProactive, setLoadingProactive] = useState(false);
  
  // Document management state
  const [allDocuments, setAllDocuments] = useState([]);
  const [addDocDialogOpen, setAddDocDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [suggestingDocs, setSuggestingDocs] = useState(false);
  const [suggestedDocs, setSuggestedDocs] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const fileInputRef = useRef(null);
  
  // Dialog states
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [viewCorrespondenceDialog, setViewCorrespondenceDialog] = useState(null);
  const [editCorrespondenceDialog, setEditCorrespondenceDialog] = useState(null);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [correspondenceToSend, setCorrespondenceToSend] = useState(null);
  const [documentViewerOpen, setDocumentViewerOpen] = useState(null);
  
  // Form states
  const [generateForm, setGenerateForm] = useState({
    response_type: 'Antwortschreiben',
    recipient: '',
    subject: '',
    instructions: '',
    document_ids: [],
    output_format: 'pdf'
  });
  const [sendForm, setSendForm] = useState({
    mail_account_id: '',
    recipient_email: ''
  });
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  const loadCaseData = async () => {
    try {
      const [caseRes, docsRes, corrRes, historyRes, mailRes] = await Promise.all([
        casesAPI.get(caseId),
        caseResponseAPI.getDocuments(caseId),
        correspondenceAPI.list(caseId),
        caseResponseAPI.getHistory(caseId),
        mailAPI.listAccounts()
      ]);
      
      setCaseData(caseRes.data);
      setDocuments(docsRes.data);
      setCorrespondence(corrRes.data);
      setHistory(historyRes.data);
      setMailAccounts(mailRes.data);
      
      // Load proactive analysis automatically
      loadProactiveAnalysis();
    } catch (error) {
      console.error('Failed to load case data:', error);
      toast.error('Falldaten konnten nicht geladen werden');
    }
    setLoading(false);
  };
  
  const loadProactiveAnalysis = async () => {
    setLoadingProactive(true);
    try {
      const response = await proactiveAI.analyzeCase(caseId);
      if (response.data.success) {
        setProactiveAnalysis(response.data);
      }
    } catch (error) {
      console.error('Failed to load proactive analysis:', error);
    }
    setLoadingProactive(false);
  };
  
  const loadAllDocuments = async () => {
    try {
      const response = await documentsAPI.list();
      // Filter out documents already in this case
      const caseDocIds = documents.map(d => d.id);
      setAllDocuments(response.data.filter(d => !caseDocIds.includes(d.id)));
    } catch (error) {
      console.error('Failed to load all documents:', error);
    }
  };
  
  const handleSuggestDocuments = async () => {
    setSuggestingDocs(true);
    setShowSuggestions(true);
    try {
      const response = await documentsAPI.suggestForCase(caseId);
      if (response.data.suggestions) {
        setSuggestedDocs(response.data.suggestions);
        if (response.data.suggestions.length === 0) {
          toast.info('Keine passenden Dokumente gefunden');
        } else {
          toast.success(`${response.data.suggestions.length} passende Dokumente gefunden`);
        }
      }
    } catch (error) {
      console.error('Failed to suggest documents:', error);
      toast.error('KI-Vorschläge konnten nicht geladen werden');
    }
    setSuggestingDocs(false);
  };
  
  const handleAddDocuments = async (docIds) => {
    if (!docIds || docIds.length === 0) {
      toast.error('Bitte wählen Sie mindestens ein Dokument aus');
      return;
    }
    try {
      await documentsAPI.assignToCase(docIds, caseId);
      toast.success(`${docIds.length} Dokument(e) hinzugefügt`);
      setAddDocDialogOpen(false);
      setShowSuggestions(false);
      setSelectedDocIds([]);
      setSuggestedDocs([]);
      loadCaseData();
    } catch (error) {
      toast.error('Hinzufügen fehlgeschlagen');
    }
  };
  
  const toggleDocSelection = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };
  
  const handleRemoveDocument = async (docId) => {
    try {
      await documentUpdateAPI.update(docId, { case_id: '' });
      toast.success('Dokument entfernt');
      loadCaseData();
    } catch (error) {
      toast.error('Entfernen fehlgeschlagen');
    }
  };
  
  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploading(true);
    try {
      for (const file of files) {
        toast.info(`Lade ${file.name} hoch...`, { id: `upload-${file.name}` });
        await documentsAPI.upload(file, caseId);
        toast.success(`${file.name} hochgeladen`, { id: `upload-${file.name}` });
      }
      loadCaseData();
    } catch (error) {
      toast.error('Upload fehlgeschlagen');
    }
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyzeCase = async () => {
    setAnalyzing(true);
    try {
      toast.info('Fall wird analysiert...', { duration: 60000, id: 'analyze' });
      const response = await caseResponseAPI.analyze(caseId);
      
      if (response.data.success) {
        setAnalysis(response.data.analysis);
        // Pre-fill form with analysis
        if (response.data.analysis) {
          setGenerateForm(prev => ({
            ...prev,
            response_type: response.data.analysis.antworttyp || prev.response_type,
            recipient: response.data.analysis.empfaenger || prev.recipient
          }));
        }
        toast.success('Analyse abgeschlossen', { id: 'analyze' });
        setGenerateDialogOpen(true);
      } else {
        toast.error(response.data.error || 'Analyse fehlgeschlagen', { id: 'analyze' });
      }
    } catch (error) {
      toast.error('Analyse fehlgeschlagen', { id: 'analyze' });
    }
    setAnalyzing(false);
  };

  const handleGenerateResponse = async () => {
    if (!generateForm.recipient || !generateForm.subject) {
      toast.error('Bitte Empfänger und Betreff angeben');
      return;
    }
    
    setGenerating(true);
    try {
      toast.info('Antwort wird generiert...', { duration: 120000, id: 'generate' });
      const response = await caseResponseAPI.generateResponse(caseId, generateForm);
      
      if (response.data.success) {
        toast.success('Antwort erfolgreich erstellt', { id: 'generate' });
        setGenerateDialogOpen(false);
        setAnalysis(null);
        loadCaseData();
        
        // Show the generated correspondence
        setViewCorrespondenceDialog({
          ...response.data,
          id: response.data.correspondence_id
        });
      } else {
        toast.error(response.data.error || 'Generierung fehlgeschlagen', { id: 'generate' });
      }
    } catch (error) {
      toast.error('Generierung fehlgeschlagen', { id: 'generate' });
    }
    setGenerating(false);
  };

  const handleDownloadCorrespondence = async (corrId) => {
    try {
      toast.info('Download wird vorbereitet...');
      const response = await correspondenceAPI.download(corrId);
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `antwort_${corrId.slice(0, 8)}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Download gestartet');
    } catch (error) {
      toast.error('Download fehlgeschlagen');
    }
  };

  const handleSendCorrespondence = async () => {
    if (!sendForm.mail_account_id || !sendForm.recipient_email) {
      toast.error('Bitte E-Mail-Konto und Empfänger angeben');
      return;
    }
    
    try {
      toast.info('E-Mail wird gesendet...', { duration: 30000, id: 'send' });
      const response = await correspondenceAPI.send(
        correspondenceToSend.id,
        sendForm.mail_account_id,
        sendForm.recipient_email
      );
      
      if (response.data.success) {
        toast.success('E-Mail erfolgreich gesendet', { id: 'send' });
        setSendDialogOpen(false);
        setCorrespondenceToSend(null);
        setSendForm({ mail_account_id: '', recipient_email: '' });
        loadCaseData();
      } else {
        toast.error(response.data.error || 'Versand fehlgeschlagen', { id: 'send' });
      }
    } catch (error) {
      toast.error('Versand fehlgeschlagen', { id: 'send' });
    }
  };

  const handleUpdateCorrespondence = async () => {
    try {
      await correspondenceAPI.update(editCorrespondenceDialog.id, {
        content: editContent
      });
      toast.success('Änderungen gespeichert');
      setEditCorrespondenceDialog(null);
      loadCaseData();
    } catch (error) {
      toast.error('Speichern fehlgeschlagen');
    }
  };

  const handleDeleteCorrespondence = async (corrId) => {
    try {
      await correspondenceAPI.delete(corrId);
      toast.success('Korrespondenz gelöscht');
      loadCaseData();
    } catch (error) {
      toast.error('Löschen fehlgeschlagen');
    }
  };

  const toggleDocumentSelection = (docId) => {
    setGenerateForm(prev => ({
      ...prev,
      document_ids: prev.document_ids.includes(docId)
        ? prev.document_ids.filter(id => id !== docId)
        : [...prev.document_ids, docId]
    }));
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="page-container">
        <Button onClick={() => navigate('/cases')} variant="ghost" className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" /> Zurück
        </Button>
        <div className="text-center py-20">
          <h3 className="text-lg font-medium text-white">Fall nicht gefunden</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container" data-testid="case-detail-page">
      {/* Header */}
      <div className="mb-8">
        <Button 
          onClick={() => navigate('/cases')} 
          variant="ghost" 
          className="text-gray-400 hover:text-white mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Zurück zu Fällen
        </Button>
        
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-white">{caseData.title}</h1>
              <span className={`px-3 py-1 rounded-full text-xs border ${STATUS_COLORS[caseData.status]}`}>
                {caseData.status === 'in_progress' ? 'In Bearbeitung' : 
                 caseData.status === 'open' ? 'Offen' :
                 caseData.status === 'waiting' ? 'Wartet' : 'Geschlossen'}
              </span>
            </div>
            {caseData.reference_number && (
              <p className="text-gray-500 font-mono text-sm">{caseData.reference_number}</p>
            )}
            {caseData.description && (
              <p className="text-gray-400 text-sm mt-2 max-w-2xl">{caseData.description}</p>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <Button 
              onClick={() => navigate(`/ai?case_id=${caseId}`)}
              className="btn-secondary flex items-center gap-2"
              data-testid="ask-ai-case-btn"
            >
              <Bot className="w-4 h-4" />
              KI fragen
            </Button>
            <Button 
              onClick={handleAnalyzeCase}
              disabled={analyzing}
              className="btn-primary flex items-center gap-2"
              data-testid="generate-response-btn"
            >
              {analyzing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Antwort generieren
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="assistant" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="assistant" className="data-[state=active]:bg-white/10">
            <Brain className="w-4 h-4 mr-2" />
            KI-Assistent
          </TabsTrigger>
          <TabsTrigger value="documents" className="data-[state=active]:bg-white/10">
            <FileText className="w-4 h-4 mr-2" />
            Dokumente ({documents.length})
          </TabsTrigger>
          <TabsTrigger value="correspondence" className="data-[state=active]:bg-white/10">
            <Mail className="w-4 h-4 mr-2" />
            Korrespondenz ({correspondence.length})
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-white/10">
            <History className="w-4 h-4 mr-2" />
            Verlauf
          </TabsTrigger>
        </TabsList>

        {/* AI Assistant Tab */}
        <TabsContent value="assistant">
          <div className="space-y-4">
            {loadingProactive ? (
              <div className="bg-[#121212] border border-white/5 rounded-xl p-8 text-center">
                <RefreshCw className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-3" />
                <p className="text-gray-400">KI analysiert den Fall...</p>
              </div>
            ) : proactiveAnalysis?.analysis ? (
              <>
                {/* Status Summary */}
                {proactiveAnalysis.analysis.status_zusammenfassung && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-[#121212] border border-white/5 rounded-xl p-5"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <Brain className="w-5 h-5 text-purple-400" />
                      </div>
                      <h3 className="text-white font-medium">Fallzusammenfassung</h3>
                    </div>
                    <p className="text-gray-300">{proactiveAnalysis.analysis.status_zusammenfassung}</p>
                  </motion.div>
                )}

                {/* Urgent Actions */}
                {proactiveAnalysis.analysis.dringende_aktionen?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-red-500/5 border border-red-500/20 rounded-xl p-5"
                  >
                    <h3 className="text-red-400 font-medium mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Dringende Aktionen
                    </h3>
                    <div className="space-y-3">
                      {proactiveAnalysis.analysis.dringende_aktionen.map((action, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-black/30 rounded-lg">
                          <span className={`px-2 py-0.5 text-xs rounded ${
                            action.prioritaet === 'hoch' ? 'bg-red-500/20 text-red-400' :
                            action.prioritaet === 'mittel' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {action.prioritaet}
                          </span>
                          <div>
                            <p className="text-white">{action.aktion}</p>
                            {action.grund && <p className="text-gray-500 text-sm mt-1">{action.grund}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Deadlines */}
                {proactiveAnalysis.analysis.erkannte_fristen?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-5"
                  >
                    <h3 className="text-amber-400 font-medium mb-3 flex items-center gap-2">
                      <Clock className="w-5 h-5" />
                      Erkannte Fristen
                    </h3>
                    <div className="space-y-2">
                      {proactiveAnalysis.analysis.erkannte_fristen.map((frist, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <Bell className="w-4 h-4 text-amber-400 mt-1 flex-shrink-0" />
                          <div>
                            <p className="text-white">{frist.frist}: {frist.aktion_erforderlich}</p>
                            {frist.quelle && <p className="text-gray-500 text-sm">Quelle: {frist.quelle}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Next Step */}
                {proactiveAnalysis.analysis.naechster_schritt && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-5"
                  >
                    <h3 className="text-blue-400 font-medium mb-3 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5" />
                      Nächster Schritt
                    </h3>
                    <p className="text-white">{proactiveAnalysis.analysis.naechster_schritt.empfehlung}</p>
                    {proactiveAnalysis.analysis.naechster_schritt.begruendung && (
                      <p className="text-gray-400 text-sm mt-2">{proactiveAnalysis.analysis.naechster_schritt.begruendung}</p>
                    )}
                    <Button 
                      onClick={handleAnalyzeCase}
                      className="btn-primary mt-4"
                      disabled={analyzing}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Antwort generieren
                    </Button>
                  </motion.div>
                )}

                {/* Additional Documents Suggestion */}
                {proactiveAnalysis.analysis.zusaetzliche_dokumente_vorschlag?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-[#121212] border border-white/5 rounded-xl p-5"
                  >
                    <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                      <FileText className="w-5 h-5 text-gray-400" />
                      Empfohlene Dokumente zum Verknüpfen
                    </h3>
                    <div className="space-y-2">
                      {proactiveAnalysis.analysis.zusaetzliche_dokumente_vorschlag.map((item, i) => (
                        <div key={i} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                          <ChevronRight className="w-4 h-4 text-gray-500" />
                          <span className="text-gray-300">{item.grund}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Missing Documents */}
                {proactiveAnalysis.analysis.fehlende_dokumente?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="bg-[#121212] border border-white/5 rounded-xl p-5"
                  >
                    <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5 text-amber-400" />
                      Möglicherweise fehlende Dokumente
                    </h3>
                    <div className="space-y-2">
                      {proactiveAnalysis.analysis.fehlende_dokumente.map((item, i) => (
                        <div key={i} className="p-3 bg-white/5 rounded-lg">
                          <p className="text-white">{item.dokument}</p>
                          {item.warum_wichtig && <p className="text-gray-500 text-sm mt-1">{item.warum_wichtig}</p>}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Warnings */}
                {proactiveAnalysis.analysis.warnungen?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="bg-orange-500/5 border border-orange-500/20 rounded-xl p-5"
                  >
                    <h3 className="text-orange-400 font-medium mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Warnungen
                    </h3>
                    <ul className="space-y-2">
                      {proactiveAnalysis.analysis.warnungen.map((warning, i) => (
                        <li key={i} className="text-orange-300 text-sm flex items-start gap-2">
                          <span className="text-orange-400">•</span>
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                )}

                {/* Refresh Button */}
                <div className="flex justify-center pt-4">
                  <Button
                    variant="ghost"
                    onClick={loadProactiveAnalysis}
                    disabled={loadingProactive}
                    className="text-gray-400"
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loadingProactive ? 'animate-spin' : ''}`} />
                    Analyse aktualisieren
                  </Button>
                </div>
              </>
            ) : (
              <div className="bg-[#121212] border border-white/5 rounded-xl p-8 text-center">
                <Brain className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 mb-4">KI-Analyse nicht verfügbar</p>
                <Button onClick={loadProactiveAnalysis} className="btn-secondary">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Analyse starten
                </Button>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <div className="space-y-4">
            {/* Document Actions */}
            <div className="flex flex-wrap gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                multiple
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp"
                className="hidden"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="btn-primary"
              >
                {uploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                Dokument hochladen
              </Button>
              <Button
                onClick={() => {
                  loadAllDocuments();
                  setSelectedDocIds([]);
                  setAddDocDialogOpen(true);
                }}
                className="btn-secondary"
              >
                <Link className="w-4 h-4 mr-2" />
                Vorhandenes verknüpfen
              </Button>
              <Button
                onClick={handleSuggestDocuments}
                disabled={suggestingDocs}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
              >
                {suggestingDocs ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                KI Vorschläge
              </Button>
            </div>
            
            {/* AI Suggestions Panel */}
            {showSuggestions && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/20 rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-medium flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    KI-Dokumentenvorschläge
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowSuggestions(false);
                      setSuggestedDocs([]);
                      setSelectedDocIds([]);
                    }}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                
                {suggestingDocs ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
                    <span className="ml-3 text-gray-400">KI analysiert Dokumente...</span>
                  </div>
                ) : suggestedDocs.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">Keine passenden Dokumente gefunden</p>
                ) : (
                  <>
                    <div className="space-y-2 max-h-64 overflow-y-auto mb-3">
                      {suggestedDocs.map((doc) => (
                        <label
                          key={doc.id}
                          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedDocIds.includes(doc.id)
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-white/10 hover:border-white/20'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedDocIds.includes(doc.id)}
                            onChange={() => toggleDocSelection(doc.id)}
                            className="mt-1 accent-purple-500"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-medium truncate">{doc.display_name}</p>
                            {doc.reason && (
                              <p className="text-purple-300 text-sm mt-1 flex items-center gap-1">
                                <Lightbulb className="w-3 h-3" />
                                {doc.reason}
                              </p>
                            )}
                            <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                              {doc.sender && <span>Von: {doc.sender}</span>}
                              {doc.document_date && <span>{doc.document_date}</span>}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                    <div className="flex justify-between items-center pt-3 border-t border-white/10">
                      <span className="text-sm text-gray-400">
                        {selectedDocIds.length} von {suggestedDocs.length} ausgewählt
                      </span>
                      <Button
                        onClick={() => handleAddDocuments(selectedDocIds)}
                        disabled={selectedDocIds.length === 0}
                        className="btn-primary"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Ausgewählte hinzufügen
                      </Button>
                    </div>
                  </>
                )}
              </motion.div>
            )}
            
            {/* Documents List */}
            <div className="space-y-3">
              {documents.length === 0 ? (
                <div className="text-center py-12 bg-[#121212] rounded-xl border border-white/5">
                  <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 mb-4">Keine Dokumente in diesem Fall</p>
                  <div className="flex justify-center gap-3">
                    <Button onClick={() => fileInputRef.current?.click()} className="btn-primary">
                      <Upload className="w-4 h-4 mr-2" /> Hochladen
                    </Button>
                    <Button onClick={() => { loadAllDocuments(); setAddDocDialogOpen(true); }} className="btn-secondary">
                      <Link className="w-4 h-4 mr-2" /> Verknüpfen
                    </Button>
                  </div>
                </div>
              ) : (
                documents.map((doc, index) => (
                  <motion.div
                    key={doc.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                    className="bg-[#121212] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-gray-400" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium truncate">
                          {doc.display_name || doc.original_filename}
                        </h3>
                        {doc.ai_summary && (
                          <p className="text-gray-400 text-sm mt-1 line-clamp-1">{doc.ai_summary}</p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                          {doc.sender && <span>{doc.sender}</span>}
                          {doc.document_date && <span>{doc.document_date}</span>}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setDocumentViewerOpen(doc)}
                          className="opacity-0 group-hover:opacity-100"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <a
                          href={documentUpdateAPI.downloadUrl(doc.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="opacity-0 group-hover:opacity-100"
                        >
                          <Button size="sm" variant="ghost">
                            <Download className="w-4 h-4" />
                          </Button>
                        </a>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleRemoveDocument(doc.id)}
                          className="opacity-0 group-hover:opacity-100 text-red-400"
                          title="Aus Fall entfernen"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </TabsContent>

        {/* Correspondence Tab */}
        <TabsContent value="correspondence">
          <div className="space-y-3">
            {correspondence.length === 0 ? (
              <div className="text-center py-12 bg-[#121212] rounded-xl border border-white/5">
                <Mail className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500">Noch keine Korrespondenz erstellt</p>
                <Button 
                  onClick={handleAnalyzeCase}
                  className="mt-4 btn-primary"
                  disabled={analyzing}
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Erste Antwort generieren
                </Button>
              </div>
            ) : (
              correspondence.map((corr, index) => (
                <motion.div
                  key={corr.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className="bg-[#121212] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-white font-medium truncate">{corr.subject}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded border ${
                          corr.status === 'sent' 
                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}>
                          {corr.status === 'sent' ? 'Gesendet' : 'Entwurf'}
                        </span>
                      </div>
                      <p className="text-gray-500 text-sm">An: {corr.recipient}</p>
                      <p className="text-gray-400 text-sm mt-1 line-clamp-2">{corr.content?.slice(0, 150)}...</p>
                      <p className="text-gray-600 text-xs mt-2">{formatDate(corr.created_at)}</p>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setViewCorrespondenceDialog(corr)}
                        className="text-gray-400"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEditCorrespondenceDialog(corr);
                          setEditContent(corr.content);
                        }}
                        className="text-gray-400"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDownloadCorrespondence(corr.id)}
                        className="text-gray-400"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                      {corr.status !== 'sent' && mailAccounts.length > 0 && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setCorrespondenceToSend(corr);
                            setSendDialogOpen(true);
                          }}
                          className="text-blue-400"
                        >
                          <Send className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteCorrespondence(corr.id)}
                        className="text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
            {history.audit_logs?.length === 0 && history.correspondence?.length === 0 ? (
              <div className="text-center py-8">
                <History className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500">Noch keine Aktivitäten</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Combine and sort by date */}
                {[...(history.correspondence || []), ...(history.audit_logs || [])]
                  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                  .slice(0, 50)
                  .map((item, index) => (
                    <div 
                      key={item.id} 
                      className="flex items-start gap-4 pb-4 border-b border-white/5 last:border-0"
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        item.type ? 'bg-blue-500/20' : 'bg-gray-500/20'
                      }`}>
                        {item.type ? (
                          <Mail className="w-4 h-4 text-blue-400" />
                        ) : (
                          <History className="w-4 h-4 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-white text-sm">
                          {item.type 
                            ? `${item.type} erstellt: ${item.subject}`
                            : `${item.action}: ${item.resource_type}`
                          }
                        </p>
                        <p className="text-gray-500 text-xs mt-1">{formatDate(item.created_at)}</p>
                      </div>
                    </div>
                  ))
                }
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Generate Response Dialog */}
      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Antwort generieren</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Analysis Results */}
            {analysis && (
              <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                <h4 className="text-purple-400 font-medium mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" /> KI-Analyse
                </h4>
                <div className="space-y-2 text-sm">
                  {analysis.antworttyp && (
                    <p><span className="text-gray-500">Empfohlene Antwort:</span> <span className="text-white">{analysis.antworttyp}</span></p>
                  )}
                  {analysis.empfaenger && (
                    <p><span className="text-gray-500">Empfänger:</span> <span className="text-white">{analysis.empfaenger}</span></p>
                  )}
                  {analysis.empfehlung && (
                    <p><span className="text-gray-500">Empfehlung:</span> <span className="text-white">{analysis.empfehlung}</span></p>
                  )}
                  {analysis.dringlichkeit && (
                    <p>
                      <span className="text-gray-500">Dringlichkeit:</span>{' '}
                      <span className={
                        analysis.dringlichkeit === 'hoch' ? 'text-red-400' :
                        analysis.dringlichkeit === 'mittel' ? 'text-amber-400' : 'text-green-400'
                      }>
                        {analysis.dringlichkeit}
                      </span>
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Form */}
            <div className="space-y-4">
              <div>
                <Label className="text-gray-300">Art des Schreibens</Label>
                <Select
                  value={generateForm.response_type}
                  onValueChange={(value) => setGenerateForm(prev => ({ ...prev, response_type: value }))}
                >
                  <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] border-white/10">
                    <SelectItem value="Antwortschreiben">Antwortschreiben</SelectItem>
                    <SelectItem value="Widerspruch">Widerspruch</SelectItem>
                    <SelectItem value="Einspruch">Einspruch</SelectItem>
                    <SelectItem value="Antrag">Antrag</SelectItem>
                    <SelectItem value="Stellungnahme">Stellungnahme</SelectItem>
                    <SelectItem value="Kündigung">Kündigung</SelectItem>
                    <SelectItem value="Mahnung">Mahnung</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className="text-gray-300">Empfänger *</Label>
                <Input
                  value={generateForm.recipient}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, recipient: e.target.value }))}
                  className="mt-1 bg-black/30 border-white/10 text-white"
                  placeholder="Name/Behörde/Unternehmen"
                />
              </div>

              <div>
                <Label className="text-gray-300">Betreff *</Label>
                <Input
                  value={generateForm.subject}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, subject: e.target.value }))}
                  className="mt-1 bg-black/30 border-white/10 text-white"
                  placeholder="z.B. Widerspruch gegen Bescheid vom..."
                />
              </div>

              <div>
                <Label className="text-gray-300">Zusätzliche Anweisungen (optional)</Label>
                <Textarea
                  value={generateForm.instructions}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, instructions: e.target.value }))}
                  className="mt-1 bg-black/30 border-white/10 text-white"
                  rows={3}
                  placeholder="Besondere Punkte die erwähnt werden sollen..."
                />
              </div>

              <div>
                <Label className="text-gray-300">Ausgabeformat</Label>
                <Select
                  value={generateForm.output_format}
                  onValueChange={(value) => setGenerateForm(prev => ({ ...prev, output_format: value }))}
                >
                  <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] border-white/10">
                    <SelectItem value="txt">Text (.txt)</SelectItem>
                    <SelectItem value="pdf">PDF (.pdf)</SelectItem>
                    <SelectItem value="docx">Word (.docx)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Document Selection */}
              {documents.length > 0 && (
                <div>
                  <Label className="text-gray-300">Dokumente als Anlagen beifügen</Label>
                  <div className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                    {documents.map(doc => (
                      <label
                        key={doc.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          generateForm.document_ids.includes(doc.id)
                            ? 'bg-blue-500/10 border-blue-500/30'
                            : 'bg-white/5 border-white/10 hover:border-white/20'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={generateForm.document_ids.includes(doc.id)}
                          onChange={() => toggleDocumentSelection(doc.id)}
                          className="sr-only"
                        />
                        <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                          generateForm.document_ids.includes(doc.id)
                            ? 'bg-blue-500 border-blue-500'
                            : 'border-white/30'
                        }`}>
                          {generateForm.document_ids.includes(doc.id) && (
                            <CheckCircle className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <span className="text-sm text-white truncate">
                          {doc.display_name || doc.original_filename}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
              <Button variant="ghost" onClick={() => setGenerateDialogOpen(false)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button
                onClick={handleGenerateResponse}
                disabled={generating || !generateForm.recipient || !generateForm.subject}
                className="btn-primary"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Wird generiert...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generieren
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Correspondence Dialog */}
      <Dialog open={!!viewCorrespondenceDialog} onOpenChange={() => setViewCorrespondenceDialog(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{viewCorrespondenceDialog?.subject}</DialogTitle>
          </DialogHeader>
          
          {viewCorrespondenceDialog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 p-4 bg-white/5 rounded-lg">
                <div>
                  <span className="text-gray-500 text-sm">An</span>
                  <p className="text-white">{viewCorrespondenceDialog.recipient}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Typ</span>
                  <p className="text-white">{viewCorrespondenceDialog.type}</p>
                </div>
              </div>
              
              <div>
                <span className="text-gray-500 text-sm">Inhalt</span>
                <pre className="mt-2 p-4 bg-black/30 rounded-lg text-gray-300 text-sm whitespace-pre-wrap font-sans max-h-96 overflow-y-auto">
                  {viewCorrespondenceDialog.content}
                </pre>
              </div>
              
              <div className="flex gap-3 pt-4 border-t border-white/5">
                <Button
                  onClick={() => handleDownloadCorrespondence(viewCorrespondenceDialog.id)}
                  className="btn-secondary"
                >
                  <Download className="w-4 h-4 mr-2" /> Herunterladen
                </Button>
                {viewCorrespondenceDialog.status !== 'sent' && mailAccounts.length > 0 && (
                  <Button
                    onClick={() => {
                      setCorrespondenceToSend(viewCorrespondenceDialog);
                      setSendDialogOpen(true);
                      setViewCorrespondenceDialog(null);
                    }}
                    className="btn-primary"
                  >
                    <Send className="w-4 h-4 mr-2" /> Per E-Mail senden
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Correspondence Dialog */}
      <Dialog open={!!editCorrespondenceDialog} onOpenChange={() => setEditCorrespondenceDialog(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-3xl max-h-[85vh]">
          <DialogHeader>
            <DialogTitle>Korrespondenz bearbeiten</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="bg-black/30 border-white/10 text-white font-mono text-sm"
              rows={20}
            />
            
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setEditCorrespondenceDialog(null)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button onClick={handleUpdateCorrespondence} className="btn-primary">
                <Save className="w-4 h-4 mr-2" /> Speichern
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Send Email Dialog */}
      <Dialog open={sendDialogOpen} onOpenChange={setSendDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>Per E-Mail senden</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-gray-300">E-Mail-Konto</Label>
              <Select
                value={sendForm.mail_account_id}
                onValueChange={(value) => setSendForm(prev => ({ ...prev, mail_account_id: value }))}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue placeholder="Konto auswählen..." />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  {mailAccounts.map(account => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.display_name} ({account.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-gray-300">Empfänger E-Mail</Label>
              <Input
                type="email"
                value={sendForm.recipient_email}
                onChange={(e) => setSendForm(prev => ({ ...prev, recipient_email: e.target.value }))}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="empfaenger@beispiel.de"
              />
            </div>
            
            {correspondenceToSend?.document_ids?.length > 0 && (
              <div className="p-3 bg-white/5 rounded-lg">
                <p className="text-gray-400 text-sm">
                  <Paperclip className="w-4 h-4 inline mr-1" />
                  {correspondenceToSend.document_ids.length} Anlage(n) werden angehängt
                </p>
              </div>
            )}
            
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setSendDialogOpen(false)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button
                onClick={handleSendCorrespondence}
                disabled={!sendForm.mail_account_id || !sendForm.recipient_email}
                className="btn-primary"
              >
                <Send className="w-4 h-4 mr-2" /> Senden
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Document Viewer Dialog */}
      <Dialog open={!!documentViewerOpen} onOpenChange={() => setDocumentViewerOpen(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{documentViewerOpen?.display_name || documentViewerOpen?.original_filename}</DialogTitle>
          </DialogHeader>
          
          {documentViewerOpen && (
            <div className="space-y-4">
              {/* Document info */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-white/5 rounded-lg text-sm">
                {documentViewerOpen.sender && (
                  <div>
                    <span className="text-gray-500">Absender</span>
                    <p className="text-white">{documentViewerOpen.sender}</p>
                  </div>
                )}
                {documentViewerOpen.document_date && (
                  <div>
                    <span className="text-gray-500">Datum</span>
                    <p className="text-white">{documentViewerOpen.document_date}</p>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Typ</span>
                  <p className="text-white capitalize">{documentViewerOpen.document_type}</p>
                </div>
              </div>
              
              {documentViewerOpen.ai_summary && (
                <div>
                  <span className="text-gray-500 text-sm">Zusammenfassung</span>
                  <p className="text-white mt-1">{documentViewerOpen.ai_summary}</p>
                </div>
              )}
              
              {/* Preview or OCR text */}
              {documentViewerOpen.mime_type?.startsWith('image/') ? (
                <div className="flex justify-center">
                  <img
                    src={documentUpdateAPI.downloadUrl(documentViewerOpen.id)}
                    alt={documentViewerOpen.display_name}
                    className="max-h-96 rounded-lg"
                  />
                </div>
              ) : documentViewerOpen.mime_type === 'application/pdf' ? (
                <iframe
                  src={documentUpdateAPI.downloadUrl(documentViewerOpen.id)}
                  className="w-full h-96 rounded-lg border border-white/10"
                  title="PDF Viewer"
                />
              ) : documentViewerOpen.ocr_text ? (
                <div>
                  <span className="text-gray-500 text-sm">Extrahierter Text</span>
                  <pre className="mt-2 p-4 bg-black/30 rounded-lg text-gray-300 text-sm whitespace-pre-wrap font-sans max-h-64 overflow-y-auto">
                    {documentViewerOpen.ocr_text}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Keine Vorschau verfügbar
                </div>
              )}
              
              {/* Tags */}
              {documentViewerOpen.tags?.length > 0 && (
                <div>
                  <span className="text-gray-500 text-sm">Tags</span>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {documentViewerOpen.tags.map((tag, i) => (
                      <span key={i} className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded border border-blue-500/20">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
                <a
                  href={documentUpdateAPI.downloadUrl(documentViewerOpen.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button className="btn-primary">
                    <Download className="w-4 h-4 mr-2" /> Herunterladen
                  </Button>
                </a>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Document Dialog */}
      <Dialog open={addDocDialogOpen} onOpenChange={(open) => {
        setAddDocDialogOpen(open);
        if (!open) setSelectedDocIds([]);
      }}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Dokumente zum Fall hinzufügen</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {allDocuments.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500">Keine weiteren Dokumente verfügbar</p>
                <p className="text-gray-600 text-sm mt-1">Alle Dokumente sind bereits diesem Fall zugeordnet oder es gibt keine weiteren.</p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-gray-400 text-sm">Wählen Sie Dokumente aus, die zu diesem Fall hinzugefügt werden sollen:</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (selectedDocIds.length === allDocuments.length) {
                        setSelectedDocIds([]);
                      } else {
                        setSelectedDocIds(allDocuments.map(d => d.id));
                      }
                    }}
                    className="text-gray-400 hover:text-white text-xs"
                  >
                    {selectedDocIds.length === allDocuments.length ? 'Alle abwählen' : 'Alle auswählen'}
                  </Button>
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {allDocuments.map((doc) => (
                    <label
                      key={doc.id}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedDocIds.includes(doc.id)
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-white/10 hover:border-white/20'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedDocIds.includes(doc.id)}
                        onChange={() => toggleDocSelection(doc.id)}
                        className="mt-1 accent-blue-500"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">
                          {doc.display_name || doc.original_filename}
                        </p>
                        {doc.ai_summary && (
                          <p className="text-gray-400 text-sm mt-1 line-clamp-1">{doc.ai_summary}</p>
                        )}
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                          {doc.sender && <span>Von: {doc.sender}</span>}
                          {doc.document_date && <span>{doc.document_date}</span>}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </>
            )}
            
            <div className="flex justify-between items-center pt-4 border-t border-white/5">
              <span className="text-sm text-gray-400">
                {selectedDocIds.length > 0 && `${selectedDocIds.length} ausgewählt`}
              </span>
              <div className="flex gap-3">
                <Button variant="ghost" onClick={() => setAddDocDialogOpen(false)} className="text-gray-400">
                  Abbrechen
                </Button>
                <Button 
                  onClick={() => handleAddDocuments(selectedDocIds)}
                  disabled={selectedDocIds.length === 0}
                  className="btn-primary"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {selectedDocIds.length} Dokument(e) hinzufügen
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
