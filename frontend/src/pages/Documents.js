import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FileText, Upload, Search, Trash2, 
  Eye, FileImage, File, MoreVertical, RefreshCw,
  Tag, Calendar, User, AlertCircle, CheckCircle,
  Loader2, Edit, Download, X, Plus, Briefcase, CheckSquare, Bot, Mail, Sparkles
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
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
import { Label } from '../components/ui/label';
import { documentsAPI, casesAPI, documentUpdateAPI, aiAPI } from '../lib/api';
import { toast } from 'sonner';

export default function Documents() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editingDoc, setEditingDoc] = useState(null);
  const [processing, setProcessing] = useState({});
  
  // Document preview state
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  
  // Upload queue state
  const [uploadQueue, setUploadQueue] = useState([]);
  const [processingQueue, setProcessingQueue] = useState([]);
  
  // Multi-select state
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [assignCaseDialogOpen, setAssignCaseDialogOpen] = useState(false);
  const [assignCaseId, setAssignCaseId] = useState('');
  
  // Suggestion dialog state
  const [suggestionDoc, setSuggestionDoc] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [selectedCaseIds, setSelectedCaseIds] = useState([]);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    display_name: '',
    document_type: '',
    tags: [],
    case_id: ''
  });

  useEffect(() => {
    loadDocuments();
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      const response = await casesAPI.list();
      setCases(response.data);
    } catch (error) {
      console.error('Failed to load cases:', error);
    }
  };

  const loadDocuments = async (search = null) => {
    try {
      const params = search ? { search } : {};
      const response = await documentsAPI.list(params);
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Dokumente konnten nicht geladen werden');
    }
    setLoading(false);
  };

  // Load document preview with token-based URL
  const loadDocumentPreview = async (doc) => {
    setLoadingPreview(true);
    setPreviewUrl(null);
    try {
      const response = await documentUpdateAPI.getDownloadToken(doc.id);
      const token = response.data.token;
      const url = documentUpdateAPI.viewUrl(doc.id, token);
      setPreviewUrl(url);
    } catch (error) {
      console.error('Failed to get preview token:', error);
      toast.error('Vorschau konnte nicht geladen werden');
    }
    setLoadingPreview(false);
  };

  // Check if document is previewable
  const isPreviewable = (mimeType) => {
    const previewableTypes = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/svg+xml'
    ];
    return previewableTypes.includes(mimeType);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    await loadDocuments(searchQuery || null);
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    let lastUploadedDoc = null;
    
    // Initialize upload queue
    const queue = Array.from(files).map((file, index) => ({
      id: index,
      name: file.name,
      status: 'waiting', // waiting, uploading, processing, done, error
      progress: 0
    }));
    setUploadQueue(queue);
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Update queue status to uploading
      setUploadQueue(prev => prev.map((item, idx) => 
        idx === i ? { ...item, status: 'uploading', progress: 30 } : item
      ));
      
      try {
        toast.info(`${file.name} wird hochgeladen...`, { duration: 10000, id: `upload-${file.name}` });
        
        // Update to processing
        setUploadQueue(prev => prev.map((item, idx) => 
          idx === i ? { ...item, status: 'processing', progress: 60 } : item
        ));
        
        const response = await documentsAPI.upload(file, null, 'other');
        
        // Update to done
        setUploadQueue(prev => prev.map((item, idx) => 
          idx === i ? { ...item, status: 'done', progress: 100 } : item
        ));
        
        if (response.data.document?.ai_analyzed) {
          toast.success(
            `${response.data.document.display_name || file.name} erfolgreich verarbeitet`, 
            { id: `upload-${file.name}` }
          );
        } else {
          toast.success(`${file.name} hochgeladen`, { id: `upload-${file.name}` });
        }
        lastUploadedDoc = response.data.document;
      } catch (error) {
        console.error('Upload error:', error);
        
        // Update to error
        setUploadQueue(prev => prev.map((item, idx) => 
          idx === i ? { ...item, status: 'error', progress: 0 } : item
        ));
        
        toast.error(`Fehler beim Hochladen von ${file.name}`, { id: `upload-${file.name}` });
      }
    }
    
    setUploading(false);
    
    // Clear queue after 3 seconds
    setTimeout(() => setUploadQueue([]), 3000);
    
    loadDocuments();
    if (fileInputRef.current) fileInputRef.current.value = '';
    
    // Show suggestion dialog for the last uploaded document
    if (lastUploadedDoc && lastUploadedDoc.id) {
      setSuggestionDoc(lastUploadedDoc);
      setLoadingSuggestions(true);
      try {
        const sugResp = await aiAPI.suggestMetadata(lastUploadedDoc.id);
        if (sugResp.data.success) {
          setSuggestions(sugResp.data);
          setSelectedTags(sugResp.data.suggested_tags || []);
          setSelectedCaseIds((sugResp.data.suggested_cases || []).map(c => c.id));
        }
      } catch (error) {
        console.error('Suggestion error:', error);
      }
      setLoadingSuggestions(false);
    }
  };

  const handleApplySuggestions = async () => {
    if (!suggestionDoc) return;
    try {
      // Update tags
      if (selectedTags.length > 0) {
        await documentUpdateAPI.update(suggestionDoc.id, { tags: selectedTags });
      }
      // Assign to cases
      for (const caseId of selectedCaseIds) {
        await documentsAPI.assignCase([suggestionDoc.id], caseId);
      }
      toast.success('Vorschläge übernommen');
      loadDocuments();
    } catch (error) {
      toast.error('Fehler beim Übernehmen');
    }
    setSuggestionDoc(null);
    setSuggestions(null);
  };

  // Handle showing AI suggestions for a document from dropdown menu
  const handleShowSuggestions = async (doc) => {
    setSuggestionDoc(doc);
    setSuggestions(null);
    setSelectedTags([]);
    setSelectedCaseIds([]);
    setLoadingSuggestions(true);
    
    try {
      const sugResp = await aiAPI.suggestMetadata(doc.id);
      if (sugResp.data.success) {
        setSuggestions(sugResp.data);
        setSelectedTags(sugResp.data.suggested_tags || []);
        setSelectedCaseIds((sugResp.data.suggested_cases || []).map(c => c.id));
      } else {
        const errorMsg = sugResp.data.error || 'KI-Vorschläge konnten nicht geladen werden';
        toast.error(errorMsg);
        // If there's no text but we still have tags/cases in response, show them
        if (sugResp.data.suggested_tags?.length > 0) {
          setSuggestions(sugResp.data);
          setSelectedTags(sugResp.data.suggested_tags || []);
        } else {
          setSuggestionDoc(null);
        }
      }
    } catch (error) {
      console.error('Suggestion error:', error);
      const msg = error.response?.data?.detail || error.response?.data?.error || 'KI-Vorschläge fehlgeschlagen. Bitte versuchen Sie "Erneut analysieren".';
      toast.error(msg);
      setSuggestionDoc(null);
    }
    setLoadingSuggestions(false);
  };

  const handleReprocess = async (doc) => {
    setProcessing(prev => ({ ...prev, [doc.id]: true }));
    try {
      toast.info('Dokument wird erneut analysiert...', { duration: 30000, id: `reprocess-${doc.id}` });
      const response = await documentsAPI.reprocess(doc.id);
      
      if (response.data.success) {
        toast.success(
          `Neuer Name: ${response.data.display_name}`,
          { id: `reprocess-${doc.id}`, duration: 5000 }
        );
        loadDocuments();
      } else {
        toast.warning(response.data.error || 'KI-Analyse fehlgeschlagen', { id: `reprocess-${doc.id}` });
      }
    } catch (error) {
      toast.error('Verarbeitung fehlgeschlagen', { id: `reprocess-${doc.id}` });
    }
    setProcessing(prev => ({ ...prev, [doc.id]: false }));
  };

  const handleDelete = async (id) => {
    try {
      await documentsAPI.delete(id);
      toast.success('Dokument gelöscht');
      loadDocuments();
    } catch (error) {
      toast.error('Löschen fehlgeschlagen');
    }
  };

  const handleEditDocument = (doc) => {
    setEditingDoc(doc);
    setEditForm({
      display_name: doc.display_name || doc.original_filename,
      document_type: doc.document_type || 'other',
      tags: doc.tags || [],
      case_id: doc.case_id || ''
    });
  };

  const handleSaveEdit = async () => {
    try {
      await documentUpdateAPI.update(editingDoc.id, editForm);
      toast.success('Dokument aktualisiert');
      setEditingDoc(null);
      loadDocuments();
    } catch (error) {
      toast.error('Speichern fehlgeschlagen');
    }
  };

  const handleAddTag = (tag) => {
    if (tag && !editForm.tags.includes(tag)) {
      setEditForm(prev => ({ ...prev, tags: [...prev.tags, tag] }));
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setEditForm(prev => ({ 
      ...prev, 
      tags: prev.tags.filter(tag => tag !== tagToRemove) 
    }));
  };
  
  // Multi-select functions
  const toggleSelection = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };
  
  const selectAll = () => {
    if (selectedDocIds.length === filteredDocuments.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(filteredDocuments.map(d => d.id));
    }
  };
  
  const handleAssignToCase = async () => {
    if (!assignCaseId || selectedDocIds.length === 0) return;
    
    try {
      for (const docId of selectedDocIds) {
        await documentUpdateAPI.update(docId, { case_id: assignCaseId });
      }
      toast.success(`${selectedDocIds.length} Dokument(e) zum Fall hinzugefügt`);
      setAssignCaseDialogOpen(false);
      setSelectedDocIds([]);
      setSelectionMode(false);
      setAssignCaseId('');
      loadDocuments();
    } catch (error) {
      toast.error('Zuweisung fehlgeschlagen');
    }
  };
  
  const handleBulkDelete = async () => {
    if (selectedDocIds.length === 0) return;
    
    if (!window.confirm(`${selectedDocIds.length} Dokument(e) wirklich löschen?`)) return;
    
    try {
      for (const docId of selectedDocIds) {
        await documentsAPI.delete(docId);
      }
      toast.success(`${selectedDocIds.length} Dokument(e) gelöscht`);
      setSelectedDocIds([]);
      setSelectionMode(false);
      loadDocuments();
    } catch (error) {
      toast.error('Löschen fehlgeschlagen');
    }
  };

  const getFileIcon = (mimeType) => {
    if (mimeType?.startsWith('image/')) return FileImage;
    if (mimeType === 'application/pdf') return FileText;
    if (mimeType?.includes('word') || mimeType?.includes('document')) return FileText;
    if (mimeType?.includes('excel') || mimeType?.includes('spreadsheet')) return FileText;
    return File;
  };
  
  const getFileIconColor = (mimeType) => {
    if (mimeType?.startsWith('image/')) return 'text-blue-400';
    if (mimeType === 'application/pdf') return 'text-red-400';
    if (mimeType?.includes('word') || mimeType?.includes('document')) return 'text-blue-500';
    if (mimeType?.includes('excel') || mimeType?.includes('spreadsheet')) return 'text-green-400';
    return 'text-gray-600';
  };
  
  const getFileTypeBadge = (mimeType) => {
    if (mimeType?.startsWith('image/')) return 'Bild';
    if (mimeType === 'application/pdf') return 'PDF';
    if (mimeType?.includes('word') || mimeType?.includes('document')) return 'Word';
    if (mimeType?.includes('excel') || mimeType?.includes('spreadsheet')) return 'Excel';
    return 'Datei';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getImportanceBadge = (importance) => {
    const colors = {
      hoch: 'bg-red-500/20 text-red-400 border-red-500/30',
      mittel: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      niedrig: 'bg-green-500/20 text-green-400 border-green-500/30'
    };
    return colors[importance] || colors.mittel;
  };
  
  // Filter documents based on search
  // Sort documents - newest first
  const sortedDocuments = [...documents].sort((a, b) => {
    const dateA = new Date(a.created_at || 0);
    const dateB = new Date(b.created_at || 0);
    return dateB - dateA;
  });
  
  const filteredDocuments = sortedDocuments;

  return (
    <div className="page-container" data-testid="documents-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('documents.title')}</h1>
          <p className="text-gray-400 text-sm">{documents.length} Dokumente</p>
        </div>
        
        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleUpload}
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.docx"
            className="hidden"
          />
          
          {/* Selection Mode Toggle */}
          <Button
            variant={selectionMode ? "default" : "ghost"}
            onClick={() => {
              setSelectionMode(!selectionMode);
              setSelectedDocIds([]);
            }}
            className={selectionMode ? "btn-secondary" : "text-gray-400"}
          >
            <CheckSquare className="w-4 h-4 mr-2" />
            {selectionMode ? 'Auswahl beenden' : 'Auswählen'}
          </Button>
          
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="btn-primary flex items-center gap-2"
            disabled={uploading}
            data-testid="upload-document-btn"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {uploading ? 'Wird verarbeitet...' : t('documents.upload')}
          </Button>
        </div>
      </div>
      
      {/* Upload Queue Progress */}
      {uploadQueue.length > 0 && (
        <div className="bg-[#121212] border border-white/10 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            <span className="text-white font-medium">Verarbeitung läuft...</span>
            <span className="text-gray-500 text-sm">
              ({uploadQueue.filter(q => q.status === 'done').length}/{uploadQueue.length} fertig)
            </span>
          </div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {uploadQueue.map((item) => (
              <div key={item.id} className="flex items-center gap-3 text-sm">
                <div className="flex-shrink-0">
                  {item.status === 'waiting' && <div className="w-4 h-4 rounded-full bg-gray-600" />}
                  {item.status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin text-blue-400" />}
                  {item.status === 'processing' && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
                  {item.status === 'done' && <CheckCircle className="w-4 h-4 text-green-400" />}
                  {item.status === 'error' && <AlertCircle className="w-4 h-4 text-red-400" />}
                </div>
                <span className={`flex-1 truncate ${item.status === 'done' ? 'text-green-400' : item.status === 'error' ? 'text-red-400' : 'text-gray-300'}`}>
                  {item.name}
                </span>
                <span className="text-xs text-gray-500 flex-shrink-0">
                  {item.status === 'waiting' && 'Wartend'}
                  {item.status === 'uploading' && 'Hochladen...'}
                  {item.status === 'processing' && 'KI-Analyse...'}
                  {item.status === 'done' && 'Fertig'}
                  {item.status === 'error' && 'Fehler'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Selection Actions Bar */}
      {selectionMode && (
        <div className="bg-[#121212] border border-white/10 rounded-xl p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedDocIds.length === filteredDocuments.length && filteredDocuments.length > 0}
                onChange={selectAll}
                className="rounded"
              />
              <span className="text-gray-300 text-sm">Alle auswählen</span>
            </label>
            <span className="text-gray-500 text-sm">
              {selectedDocIds.length} von {filteredDocuments.length} ausgewählt
            </span>
          </div>
          
          {selectedDocIds.length > 0 && (
            <div className="flex items-center gap-3">
              <Button
                onClick={() => setAssignCaseDialogOpen(true)}
                className="btn-secondary"
              >
                <Briefcase className="w-4 h-4 mr-2" />
                Zu Fall hinzufügen
              </Button>
              <Button
                variant="ghost"
                onClick={handleBulkDelete}
                className="text-red-400 hover:bg-red-500/10"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Löschen
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="Suche in Dokumenteninhalt und Namen... (z.B. 'Steuern 2024')"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-[#121212] border-white/10 text-white"
            data-testid="search-documents-input"
          />
        </div>
        <Button type="submit" variant="secondary" className="btn-secondary">
          Suchen
        </Button>
        {searchQuery && (
          <Button 
            type="button" 
            variant="ghost" 
            onClick={() => { setSearchQuery(''); loadDocuments(); }}
            className="text-gray-400"
          >
            Zurücksetzen
          </Button>
        )}
      </form>

      {/* Documents Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : documents.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">
            {searchQuery ? 'Keine Treffer gefunden' : t('documents.noDocuments')}
          </h3>
          <p className="text-gray-500">
            {searchQuery 
              ? 'Versuchen Sie einen anderen Suchbegriff'
              : t('documents.uploadFirst')
            }
          </p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredDocuments.map((doc, index) => {
            const FileIcon = getFileIcon(doc.mime_type);
            const fileIconColor = getFileIconColor(doc.mime_type);
            const fileTypeBadge = getFileTypeBadge(doc.mime_type);
            const isProcessing = processing[doc.id];
            const isSelected = selectedDocIds.includes(doc.id);
            
            // Determine source
            const source = doc.source === 'email' || doc.email_id ? 'E-Mail' : 'Upload';
            const sourceIcon = source === 'E-Mail' ? Mail : Upload;
            const SourceIcon = sourceIcon;
            
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.02 }}
                onClick={() => !selectionMode && setSelectedDoc(doc)}
                className={`bg-[#121212] border rounded-xl overflow-hidden hover:border-white/20 transition-all cursor-pointer group ${
                  isSelected ? 'border-blue-500/50 bg-blue-500/5 ring-2 ring-blue-500/30' : 'border-white/5'
                }`}
                data-testid={`document-card-${index}`}
              >
                {/* Document Preview / Icon Header */}
                <div className="relative h-32 bg-gradient-to-br from-white/5 to-white/[0.02] flex flex-col items-center justify-center">
                  {/* Selection Checkbox */}
                  {selectionMode && (
                    <div 
                      className="absolute top-2 left-2 z-10"
                      onClick={(e) => { e.stopPropagation(); toggleSelection(doc.id); }}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="w-5 h-5 rounded cursor-pointer"
                      />
                    </div>
                  )}
                  
                  {/* File Icon with improved colors */}
                  <FileIcon className={`w-16 h-16 ${fileIconColor} group-hover:scale-110 transition-transform`} />
                  
                  {/* File Type Badge */}
                  <span className="mt-2 px-2 py-0.5 bg-white/10 text-gray-300 text-xs rounded">
                    {fileTypeBadge}
                  </span>
                  
                  {/* Status Badges - Top Right */}
                  <div className="absolute top-2 right-2 flex flex-col gap-1">
                    {doc.ai_analyzed && (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded backdrop-blur-sm">
                        <CheckCircle className="w-3 h-3" /> KI
                      </span>
                    )}
                    {doc.case_id && (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded backdrop-blur-sm">
                        <Briefcase className="w-3 h-3" />
                      </span>
                    )}
                  </div>
                  
                  {/* Source Badge - Bottom Left */}
                  <div className="absolute bottom-2 left-2">
                    <span className={`flex items-center gap-1 px-2 py-0.5 text-xs rounded backdrop-blur-sm ${
                      source === 'E-Mail' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      <SourceIcon className="w-3 h-3" />
                      {source}
                    </span>
                  </div>
                  
                  {/* Processing Overlay */}
                  {isProcessing && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                    </div>
                  )}
                </div>
                
                {/* Document Info */}
                <div className="p-3">
                  {/* Title */}
                  <h3 className="text-white font-medium text-sm truncate mb-1" title={doc.display_name || doc.original_filename}>
                    {doc.display_name || doc.original_filename}
                  </h3>
                  
                  {/* Summary */}
                  {doc.ai_summary && (
                    <p className="text-gray-500 text-xs line-clamp-2 mb-2">{doc.ai_summary}</p>
                  )}
                  
                  {/* Meta Info */}
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString('de-DE') : 'Unbekannt'}
                    </span>
                    <span>{doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB` : ''}</span>
                  </div>
                  
                  {/* Tags */}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {doc.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="px-1.5 py-0.5 bg-white/5 text-gray-400 text-xs rounded">
                          {tag}
                        </span>
                      ))}
                      {doc.tags.length > 3 && (
                        <span className="text-gray-600 text-xs">+{doc.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Quick Actions - Hidden until hover */}
                <div className="border-t border-white/5 p-2 flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-7 w-7 p-0 text-gray-400 hover:text-white"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDownload(doc); }} className="text-gray-300 focus:bg-white/10">
                        <Download className="w-4 h-4 mr-2" /> Download
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setEditingDoc(doc); }} className="text-gray-300 focus:bg-white/10">
                        <Edit className="w-4 h-4 mr-2" /> Bearbeiten
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleShowSuggestions(doc); }} className="text-gray-300 focus:bg-white/10">
                        <Sparkles className="w-4 h-4 mr-2" /> KI-Vorschläge
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }} 
                        className="text-red-400 focus:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> Löschen
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Document Detail Dialog */}
      <Dialog open={!!selectedDoc} onOpenChange={() => { setSelectedDoc(null); setPreviewUrl(null); }}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Dokumentdetails</DialogTitle>
          </DialogHeader>
          
          {selectedDoc && (
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-white">{selectedDoc.display_name}</h3>
                  <p className="text-gray-500 text-sm">Original: {selectedDoc.original_filename}</p>
                </div>
                {isPreviewable(selectedDoc.mime_type) && !previewUrl && (
                  <Button
                    onClick={() => loadDocumentPreview(selectedDoc)}
                    disabled={loadingPreview}
                    className="btn-secondary"
                  >
                    {loadingPreview ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Eye className="w-4 h-4 mr-2" />
                    )}
                    Vorschau
                  </Button>
                )}
              </div>
              
              {/* Document Preview */}
              {previewUrl && (
                <div className="border border-white/10 rounded-lg overflow-hidden bg-white">
                  {selectedDoc.mime_type === 'application/pdf' ? (
                    <iframe
                      src={previewUrl}
                      className="w-full h-[500px]"
                      title="Document Preview"
                    />
                  ) : selectedDoc.mime_type?.startsWith('image/') ? (
                    <img
                      src={previewUrl}
                      alt={selectedDoc.display_name}
                      className="max-w-full max-h-[500px] object-contain mx-auto"
                    />
                  ) : null}
                </div>
              )}
              
              {selectedDoc.ai_summary && (
                <div>
                  <label className="text-gray-400 text-sm">Zusammenfassung</label>
                  <p className="text-white mt-1">{selectedDoc.ai_summary}</p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                {selectedDoc.sender && (
                  <div>
                    <label className="text-gray-400 text-sm">Absender</label>
                    <p className="text-white">{selectedDoc.sender}</p>
                  </div>
                )}
                {selectedDoc.document_date && (
                  <div>
                    <label className="text-gray-400 text-sm">Datum</label>
                    <p className="text-white">{selectedDoc.document_date}</p>
                  </div>
                )}
                <div>
                  <label className="text-gray-400 text-sm">Dokumenttyp</label>
                  <p className="text-white capitalize">{selectedDoc.document_type}</p>
                </div>
                <div>
                  <label className="text-gray-400 text-sm">Wichtigkeit</label>
                  <p className="text-white capitalize">{selectedDoc.importance || 'Mittel'}</p>
                </div>
              </div>
              
              {selectedDoc.tags && selectedDoc.tags.length > 0 && (
                <div>
                  <label className="text-gray-400 text-sm">Tags</label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedDoc.tags.map((tag, i) => (
                      <span 
                        key={i}
                        className="px-2 py-1 bg-blue-500/10 text-blue-400 text-sm rounded border border-blue-500/20"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {!previewUrl && selectedDoc.ocr_text && (
                <div>
                  <label className="text-gray-400 text-sm">OCR-Text (Auszug)</label>
                  <pre className="mt-1 p-3 bg-black/30 rounded text-gray-300 text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">
                    {selectedDoc.ocr_text.slice(0, 1000)}
                    {selectedDoc.ocr_text.length > 1000 && '...'}
                  </pre>
                </div>
              )}
              
              {selectedDoc.metadata && Object.keys(selectedDoc.metadata).length > 0 && (
                <div>
                  <label className="text-gray-400 text-sm">Metadaten</label>
                  <pre className="mt-1 p-3 bg-black/30 rounded text-gray-300 text-xs overflow-x-auto">
                    {JSON.stringify(selectedDoc.metadata, null, 2)}
                  </pre>
                </div>
              )}
              
              <div className="flex gap-3 pt-4 border-t border-white/5">
                <Button
                  onClick={async () => {
                    try {
                      const response = await documentUpdateAPI.getDownloadToken(selectedDoc.id);
                      const token = response.data.token;
                      const url = documentUpdateAPI.viewUrl(selectedDoc.id, token);
                      window.open(url, '_blank');
                    } catch (error) {
                      toast.error('Download fehlgeschlagen');
                    }
                  }}
                  className="btn-primary"
                >
                  <Download className="w-4 h-4 mr-2" /> Herunterladen
                </Button>
                <Button 
                  variant="secondary" 
                  onClick={() => {
                    handleEditDocument(selectedDoc);
                    setSelectedDoc(null);
                  }}
                  className="btn-secondary"
                >
                  <Edit className="w-4 h-4 mr-2" /> Bearbeiten
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Document Dialog */}
      <Dialog open={!!editingDoc} onOpenChange={() => setEditingDoc(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle>Dokument bearbeiten</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-gray-300">Anzeigename</Label>
              <Input
                value={editForm.display_name}
                onChange={(e) => setEditForm(prev => ({ ...prev, display_name: e.target.value }))}
                className="mt-1 bg-black/30 border-white/10 text-white"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Dokumenttyp</Label>
              <Select
                value={editForm.document_type}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, document_type: value }))}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  <SelectItem value="letter">Brief</SelectItem>
                  <SelectItem value="invoice">Rechnung</SelectItem>
                  <SelectItem value="contract">Vertrag</SelectItem>
                  <SelectItem value="form">Formular</SelectItem>
                  <SelectItem value="receipt">Beleg</SelectItem>
                  <SelectItem value="id_document">Ausweisdokument</SelectItem>
                  <SelectItem value="other">Sonstiges</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-gray-300">Fall zuweisen</Label>
              <Select
                value={editForm.case_id || "none"}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, case_id: value === "none" ? "" : value }))}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue placeholder="Kein Fall" />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  <SelectItem value="none">Kein Fall</SelectItem>
                  {cases.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label className="text-gray-300">Tags</Label>
              <div className="flex flex-wrap gap-1 mt-2 mb-2">
                {editForm.tags.map((tag, i) => (
                  <span 
                    key={i}
                    className="flex items-center gap-1 px-2 py-1 bg-blue-500/10 text-blue-400 text-sm rounded border border-blue-500/20"
                  >
                    {tag}
                    <button onClick={() => handleRemoveTag(tag)} className="hover:text-blue-200">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  id="new-tag-input"
                  placeholder="Neuen Tag hinzufügen..."
                  className="bg-black/30 border-white/10 text-white"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag(e.target.value);
                      e.target.value = '';
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    const input = document.getElementById('new-tag-input');
                    handleAddTag(input.value);
                    input.value = '';
                  }}
                  className="text-gray-400"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setEditingDoc(null)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button onClick={handleSaveEdit} className="btn-primary">
                Speichern
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Assign to Case Dialog */}
      <Dialog open={assignCaseDialogOpen} onOpenChange={setAssignCaseDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-md">
          <DialogHeader>
            <DialogTitle>Dokumente zu Fall hinzufügen</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p className="text-gray-400 text-sm">
              {selectedDocIds.length} Dokument(e) werden dem ausgewählten Fall zugeordnet.
            </p>
            
            <div>
              <Label className="text-gray-300">Fall auswählen</Label>
              <Select
                value={assignCaseId}
                onValueChange={setAssignCaseId}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue placeholder="Fall auswählen..." />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  {cases.map(c => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.title}
                      {c.reference_number && ` (${c.reference_number})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {cases.length === 0 && (
              <p className="text-amber-400 text-sm">
                Keine Fälle vorhanden. Erstellen Sie zuerst einen Fall.
              </p>
            )}
            
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setAssignCaseDialogOpen(false)} className="text-gray-400">
                Abbrechen
              </Button>
              <Button 
                onClick={handleAssignToCase} 
                disabled={!assignCaseId}
                className="btn-primary"
              >
                <Briefcase className="w-4 h-4 mr-2" />
                Zuweisen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Suggestion Dialog after Upload */}
      <Dialog open={!!suggestionDoc} onOpenChange={(open) => { if (!open) { setSuggestionDoc(null); setSuggestions(null); } }}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Tag className="w-5 h-5 text-purple-400" />
              KI-Vorschläge
            </DialogTitle>
          </DialogHeader>
          
          {loadingSuggestions ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
              <span className="text-gray-400 text-sm ml-3">KI analysiert Dokument...</span>
            </div>
          ) : suggestions ? (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Für: <span className="text-white font-medium">{suggestionDoc?.display_name || suggestionDoc?.original_filename}</span>
              </p>
              
              {suggestions.reasoning && (
                <p className="text-gray-500 text-xs bg-purple-500/5 border border-purple-500/10 rounded p-2">{suggestions.reasoning}</p>
              )}

              {/* Tags */}
              <div>
                <p className="text-gray-300 text-sm font-medium mb-2">Tags:</p>
                <div className="flex flex-wrap gap-2">
                  {(suggestions.suggested_tags || []).map((tag) => (
                    <button
                      key={tag}
                      onClick={() => setSelectedTags(prev => 
                        prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
                      )}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        selectedTags.includes(tag)
                          ? 'bg-purple-500/30 text-purple-200 border border-purple-500/50'
                          : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                      }`}
                      data-testid={`suggest-tag-${tag}`}
                    >
                      {selectedTags.includes(tag) ? <CheckSquare className="w-3 h-3 inline mr-1" /> : null}
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Cases */}
              {suggestions.suggested_cases && suggestions.suggested_cases.length > 0 && (
                <div>
                  <p className="text-gray-300 text-sm font-medium mb-2">Passende Fälle:</p>
                  <div className="space-y-2">
                    {suggestions.suggested_cases.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => setSelectedCaseIds(prev =>
                          prev.includes(c.id) ? prev.filter(id => id !== c.id) : [...prev, c.id]
                        )}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 ${
                          selectedCaseIds.includes(c.id)
                            ? 'bg-amber-500/20 text-amber-200 border border-amber-500/30'
                            : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                        }`}
                        data-testid={`suggest-case-${c.id}`}
                      >
                        {selectedCaseIds.includes(c.id) && <CheckSquare className="w-4 h-4 flex-shrink-0" />}
                        <Briefcase className="w-4 h-4 flex-shrink-0" />
                        <span>{c.title}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="ghost" onClick={() => { setSuggestionDoc(null); setSuggestions(null); }} className="text-gray-400">
                  Überspringen
                </Button>
                <Button onClick={handleApplySuggestions} className="btn-primary" data-testid="apply-suggestions-btn">
                  <CheckCircle className="w-4 h-4 mr-2" /> Übernehmen
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm text-center py-4">Keine Vorschläge verfügbar</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
