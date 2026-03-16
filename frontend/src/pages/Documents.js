import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  FileText, Upload, Search, Trash2, 
  Eye, FileImage, File, MoreVertical, RefreshCw,
  Tag, Calendar, User, AlertCircle, CheckCircle,
  Loader2, Edit, Download, X, Plus
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
import { documentsAPI, casesAPI, documentUpdateAPI } from '../lib/api';
import { toast } from 'sonner';

export default function Documents() {
  const { t, i18n } = useTranslation();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editingDoc, setEditingDoc] = useState(null);
  const [processing, setProcessing] = useState({});
  
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

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    await loadDocuments(searchQuery || null);
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    
    for (const file of files) {
      try {
        toast.info(`${file.name} wird verarbeitet...`, { duration: 10000, id: `upload-${file.name}` });
        const response = await documentsAPI.upload(file, null, 'other');
        
        if (response.data.document?.ai_analyzed) {
          toast.success(
            `${response.data.document.display_name || file.name} erfolgreich verarbeitet`, 
            { id: `upload-${file.name}` }
          );
        } else {
          toast.success(`${file.name} hochgeladen`, { id: `upload-${file.name}` });
        }
      } catch (error) {
        console.error('Upload error:', error);
        toast.error(`Fehler beim Hochladen von ${file.name}`, { id: `upload-${file.name}` });
      }
    }
    
    setUploading(false);
    loadDocuments();
    if (fileInputRef.current) fileInputRef.current.value = '';
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

  const getFileIcon = (mimeType) => {
    if (mimeType?.startsWith('image/')) return FileImage;
    return File;
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
        <div className="space-y-3">
          {documents.map((doc, index) => {
            const FileIcon = getFileIcon(doc.mime_type);
            const isProcessing = processing[doc.id];
            
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="bg-[#121212] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors group"
                data-testid={`document-card-${index}`}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileIcon className="w-6 h-6 text-gray-400" />
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {/* Title */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <h3 className="text-white font-medium truncate">
                          {doc.display_name || doc.original_filename}
                        </h3>
                        {doc.display_name && doc.display_name !== doc.original_filename && (
                          <p className="text-gray-600 text-xs truncate">
                            Original: {doc.original_filename}
                          </p>
                        )}
                      </div>
                      
                      {/* Status badges */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {doc.ai_analyzed && (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded border border-green-500/20">
                            <CheckCircle className="w-3 h-3" /> KI
                          </span>
                        )}
                        {doc.importance && (
                          <span className={`px-2 py-0.5 text-xs rounded border ${getImportanceBadge(doc.importance)}`}>
                            {doc.importance}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Summary */}
                    {doc.ai_summary && (
                      <p className="text-gray-400 text-sm mt-1 line-clamp-2">{doc.ai_summary}</p>
                    )}
                    
                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500">
                      {doc.sender && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" /> {doc.sender}
                        </span>
                      )}
                      {doc.document_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" /> {doc.document_date}
                        </span>
                      )}
                      <span>{formatFileSize(doc.size)}</span>
                      <span className="capitalize">{doc.document_type}</span>
                    </div>
                    
                    {/* Tags */}
                    {doc.tags && doc.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {doc.tags.slice(0, 5).map((tag, i) => (
                          <span 
                            key={i}
                            className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded border border-blue-500/20"
                          >
                            {tag}
                          </span>
                        ))}
                        {doc.tags.length > 5 && (
                          <span className="text-gray-500 text-xs">+{doc.tags.length - 5}</span>
                        )}
                      </div>
                    )}
                    
                    {/* Deadlines warning */}
                    {doc.deadlines && doc.deadlines.length > 0 && (
                      <div className="flex items-center gap-2 mt-2 p-2 bg-amber-500/10 border border-amber-500/20 rounded">
                        <AlertCircle className="w-4 h-4 text-amber-400" />
                        <span className="text-amber-400 text-xs">
                          Frist(en): {doc.deadlines.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical className="w-4 h-4 text-gray-400" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                      <DropdownMenuItem 
                        onClick={() => setSelectedDoc(doc)}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <Eye className="w-4 h-4 mr-2" /> Details anzeigen
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => handleEditDocument(doc)}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <Edit className="w-4 h-4 mr-2" /> Bearbeiten
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => handleReprocess(doc)}
                        disabled={isProcessing}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <RefreshCw className={`w-4 h-4 mr-2 ${isProcessing ? 'animate-spin' : ''}`} /> 
                        Erneut analysieren
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild className="text-gray-300 focus:bg-white/10">
                        <a 
                          href={documentUpdateAPI.downloadUrl(doc.id)} 
                          target="_blank" 
                          rel="noopener noreferrer"
                        >
                          <Download className="w-4 h-4 mr-2" /> Herunterladen
                        </a>
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => handleDelete(doc.id)}
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
      <Dialog open={!!selectedDoc} onOpenChange={() => setSelectedDoc(null)}>
        <DialogContent className="bg-[#121212] border-white/10 text-white max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Dokumentdetails</DialogTitle>
          </DialogHeader>
          
          {selectedDoc && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{selectedDoc.display_name}</h3>
                <p className="text-gray-500 text-sm">Original: {selectedDoc.original_filename}</p>
              </div>
              
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
              
              {selectedDoc.ocr_text && (
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
                <a
                  href={documentUpdateAPI.downloadUrl(selectedDoc.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button className="btn-primary">
                    <Download className="w-4 h-4 mr-2" /> Herunterladen
                  </Button>
                </a>
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
                value={editForm.case_id}
                onValueChange={(value) => setEditForm(prev => ({ ...prev, case_id: value }))}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white">
                  <SelectValue placeholder="Kein Fall" />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  <SelectItem value="">Kein Fall</SelectItem>
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
    </div>
  );
}
