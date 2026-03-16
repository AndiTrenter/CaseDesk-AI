import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Briefcase, Plus, Search, MoreVertical, Trash2, 
  Edit, FileText, Mail, CheckSquare, ExternalLink, Sparkles
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { casesAPI, aiAPI, documentsAPI } from '../lib/api';
import { toast } from 'sonner';

const STATUS_COLORS = {
  open: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  in_progress: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  waiting: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  closed: 'bg-gray-500/10 text-gray-400 border-gray-500/20'
};

export default function Cases() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    reference_number: '',
    status: 'open'
  });
  
  // AI Suggestions state
  const [suggestions, setSuggestions] = useState(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState([]);

  useEffect(() => {
    loadCases();
  }, []);
  
  // Debounced AI suggestions when title/description changes
  useEffect(() => {
    if (!editingCase && formData.title.length > 5) {
      const timer = setTimeout(() => {
        loadSuggestions();
      }, 1500); // Wait 1.5 seconds after typing
      return () => clearTimeout(timer);
    }
  }, [formData.title, formData.description]);
  
  const loadSuggestions = async () => {
    if (!formData.title) return;
    
    setLoadingSuggestions(true);
    try {
      const response = await aiAPI.suggestDocuments(formData.title, formData.description);
      if (response.data.success) {
        setSuggestions(response.data);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
    setLoadingSuggestions(false);
  };

  const loadCases = async () => {
    try {
      const response = await casesAPI.list();
      setCases(response.data);
    } catch (error) {
      console.error('Failed to load cases:', error);
      toast.error('Failed to load cases');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      let newCaseId = null;
      
      if (editingCase) {
        await casesAPI.update(editingCase.id, formData);
        toast.success('Fall aktualisiert');
      } else {
        const response = await casesAPI.create(formData);
        newCaseId = response.data.id;
        toast.success('Fall erstellt');
        
        // Auto-link selected documents
        if (selectedDocIds.length > 0 && newCaseId) {
          for (const docId of selectedDocIds) {
            try {
              await documentsAPI.update(docId, { case_id: newCaseId });
            } catch (err) {
              console.error('Failed to link document:', err);
            }
          }
          toast.success(`${selectedDocIds.length} Dokumente automatisch verknüpft`);
        }
      }
      
      setIsDialogOpen(false);
      setEditingCase(null);
      setFormData({ title: '', description: '', reference_number: '', status: 'open' });
      setSuggestions(null);
      setSelectedDocIds([]);
      loadCases();
      
      // Navigate to new case if created
      if (newCaseId) {
        navigate(`/cases/${newCaseId}`);
      }
    } catch (error) {
      toast.error('Speichern fehlgeschlagen');
    }
  };

  const handleEdit = (caseItem) => {
    setEditingCase(caseItem);
    setFormData({
      title: caseItem.title,
      description: caseItem.description || '',
      reference_number: caseItem.reference_number || '',
      status: caseItem.status
    });
    setSuggestions(null);
    setSelectedDocIds([]);
    setIsDialogOpen(true);
  };
  
  const toggleDocSelection = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  const handleDelete = async (id) => {
    try {
      await casesAPI.delete(id);
      toast.success('Case deleted');
      loadCases();
    } catch (error) {
      toast.error('Failed to delete case');
    }
  };

  const filteredCases = cases.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="page-container" data-testid="cases-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('cases.title')}</h1>
          <p className="text-gray-400 text-sm">{cases.length} {t('cases.title').toLowerCase()}</p>
        </div>
        
        <Button
          onClick={() => {
            setEditingCase(null);
            setFormData({ title: '', description: '', reference_number: '', status: 'open' });
            setIsDialogOpen(true);
          }}
          className="btn-primary flex items-center gap-2"
          data-testid="create-case-btn"
        >
          <Plus className="w-4 h-4" />
          {t('cases.create')}
        </Button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder={t('cases.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-[#121212] border-white/10 text-white"
            data-testid="search-cases-input"
          />
        </div>
      </div>

      {/* Cases List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : filteredCases.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Briefcase className="w-8 h-8 text-gray-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">{t('cases.noCases')}</h3>
          <p className="text-gray-500">{t('cases.createFirst')}</p>
        </motion.div>
      ) : (
        <div className="space-y-4">
          {filteredCases.map((caseItem, index) => (
            <motion.div
              key={caseItem.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-5 hover:border-white/10 transition-colors group cursor-pointer"
              onClick={() => navigate(`/cases/${caseItem.id}`)}
              data-testid={`case-item-${index}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-white font-medium">{caseItem.title}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[caseItem.status]}`}>
                      {t(`cases.${caseItem.status === 'in_progress' ? 'inProgress' : caseItem.status}`)}
                    </span>
                  </div>
                  
                  {caseItem.description && (
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">{caseItem.description}</p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {caseItem.reference_number && (
                      <span className="font-mono">{caseItem.reference_number}</span>
                    )}
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" /> {caseItem.document_ids?.length || 0}
                    </span>
                    <span className="flex items-center gap-1">
                      <Mail className="w-3 h-3" /> {caseItem.email_ids?.length || 0}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/cases/${caseItem.id}`);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-blue-400"
                  >
                    <Sparkles className="w-4 h-4 mr-1" /> Antwort
                  </Button>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical className="w-4 h-4 text-gray-400" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                      <DropdownMenuItem 
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/cases/${caseItem.id}`);
                        }}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" /> Öffnen
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEdit(caseItem);
                        }}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <Edit className="w-4 h-4 mr-2" /> {t('common.edit')}
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(caseItem.id);
                        }}
                        className="text-red-400 focus:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> {t('common.delete')}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>{editingCase ? t('common.edit') : t('cases.create')}</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-gray-300">Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                required
                data-testid="case-title-input"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                rows={3}
                data-testid="case-description-input"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Reference Number</Label>
              <Input
                value={formData.reference_number}
                onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white font-mono"
                placeholder="e.g., CASE-2024-001"
                data-testid="case-reference-input"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">{t('cases.status')}</Label>
              <Select
                value={formData.status}
                onValueChange={(value) => setFormData({ ...formData, status: value })}
              >
                <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white" data-testid="case-status-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  <SelectItem value="open">{t('cases.open')}</SelectItem>
                  <SelectItem value="in_progress">{t('cases.inProgress')}</SelectItem>
                  <SelectItem value="waiting">{t('cases.waiting')}</SelectItem>
                  <SelectItem value="closed">{t('cases.closed')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* AI Document Suggestions */}
            {!editingCase && (loadingSuggestions || suggestions) && (
              <div className="pt-4 border-t border-white/10">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className={`w-4 h-4 text-purple-400 ${loadingSuggestions ? 'animate-pulse' : ''}`} />
                  <span className="text-sm text-gray-300 font-medium">
                    {loadingSuggestions ? 'KI sucht relevante Dokumente...' : 'KI-Dokumentenvorschläge'}
                  </span>
                </div>
                
                {suggestions?.suggestions?.length > 0 && (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {suggestions.suggestions.map((doc) => (
                      <label
                        key={doc.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedDocIds.includes(doc.id)
                            ? 'bg-purple-500/10 border-purple-500/30'
                            : 'bg-white/5 border-white/10 hover:border-white/20'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedDocIds.includes(doc.id)}
                          onChange={() => toggleDocSelection(doc.id)}
                          className="mt-1"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate">
                            {doc.display_name || doc.original_filename}
                          </p>
                          {doc.relevanz && (
                            <p className="text-purple-400 text-xs mt-1">{doc.relevanz}</p>
                          )}
                          {doc.sender && (
                            <p className="text-gray-500 text-xs">Von: {doc.sender}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
                
                {suggestions?.analysis?.empfohlene_aktionen?.length > 0 && (
                  <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <p className="text-blue-300 text-xs font-medium mb-1">Empfohlene Aktionen:</p>
                    <ul className="text-blue-200 text-xs space-y-1">
                      {suggestions.analysis.empfohlene_aktionen.map((action, i) => (
                        <li key={i}>• {action}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {selectedDocIds.length > 0 && (
                  <p className="text-purple-400 text-xs mt-2">
                    {selectedDocIds.length} Dokument(e) werden automatisch verknüpft
                  </p>
                )}
              </div>
            )}
            
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setIsDialogOpen(false);
                  setSuggestions(null);
                  setSelectedDocIds([]);
                }}
                className="text-gray-400"
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" className="btn-primary" data-testid="save-case-btn">
                {t('common.save')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
