import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Brain, FileText, Briefcase, Trash2, X, User, Save,
  ChevronDown, ChevronUp, Loader2, AlertCircle, Edit, ShieldAlert, Lock
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { aiAPI } from '../lib/api';
import { toast } from 'sonner';

export default function AIKnowledge() {
  const [knowledge, setKnowledge] = useState(null);
  const [onboarding, setOnboarding] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [showDocs, setShowDocs] = useState(false);
  const [showCases, setShowCases] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [knowledgeRes, onboardingRes] = await Promise.all([
        aiAPI.getKnowledge(),
        aiAPI.getOnboarding()
      ]);
      setKnowledge(knowledgeRes.data);
      setOnboarding(onboardingRes.data.profile || {});
    } catch (error) {
      console.error('Failed to load:', error);
    }
    setLoading(false);
  };

  const handleSaveOnboarding = async () => {
    setSaving(true);
    try {
      await aiAPI.saveOnboarding(onboarding);
      toast.success('Basisprofil gespeichert');
      setEditMode(false);
      loadAll();
    } catch (error) {
      toast.error('Fehler beim Speichern');
    }
    setSaving(false);
  };

  const handleDeleteFact = async (index) => {
    try {
      await aiAPI.deleteProfileFact(index);
      toast.success('Fakt entfernt');
      loadAll();
    } catch (error) {
      toast.error('Fehler beim Entfernen');
    }
  };

  const handleClearMemory = async () => {
    if (!deletePassword.trim()) {
      toast.error('Bitte geben Sie Ihr Passwort ein');
      return;
    }
    setDeleting(true);
    try {
      const formData = new FormData();
      formData.append('password', deletePassword);
      const response = await aiAPI.clearProfile(deletePassword);
      if (response.data.success) {
        toast.success(`KI-Gedächtnis gelöscht (${response.data.deleted_facts} Fakten entfernt)`);
        setDeleteDialogOpen(false);
        setDeletePassword('');
        loadAll();
      } else {
        toast.error(response.data.error || 'Löschen fehlgeschlagen');
      }
    } catch (error) {
      toast.error('Falsches Passwort oder Fehler beim Löschen');
    }
    setDeleting(false);
  };

  const onboardingFields = [
    { key: 'full_name', label: 'Vollständiger Name', placeholder: 'Max Mustermann' },
    { key: 'address', label: 'Adresse', placeholder: 'Musterstr. 1, 12345 Berlin' },
    { key: 'phone', label: 'Telefonnummer', placeholder: '+49 123 456789' },
    { key: 'birthdate', label: 'Geburtsdatum', placeholder: '01.01.1990' },
    { key: 'marital_status', label: 'Familienstand', placeholder: 'Verheiratet / Ledig / ...' },
    { key: 'partner_name', label: 'Partner / Ehepartner', placeholder: 'Name des Partners' },
    { key: 'children', label: 'Kinder', placeholder: 'z.B. 2 (Lisa 5, Max 8)' },
    { key: 'employer', label: 'Arbeitgeber', placeholder: 'Firma GmbH' },
    { key: 'occupation', label: 'Beruf / Position', placeholder: 'Softwareentwickler' },
    { key: 'insurance_health', label: 'Krankenversicherung', placeholder: 'AOK / TK / ...' },
    { key: 'notes', label: 'Sonstige Informationen', placeholder: 'Allergien, besondere Umstände...' },
  ];

  if (loading) {
    return (
      <div className="page-container flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
      </div>
    );
  }

  const profile = knowledge?.profile || {};
  const facts = profile.facts || [];

  return (
    <div className="page-container" data-testid="ai-knowledge-page">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-purple-400" />
            </div>
            KI-Wissen
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Alles was die KI über Sie weiß - aus Ihrem Profil, Dokumenten und Gesprächen gelernt
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-[#121212] border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">{facts.length}</p>
            <p className="text-gray-500 text-sm">Gelernte Fakten</p>
          </div>
          <div className="bg-[#121212] border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-blue-400">{knowledge?.documents_analyzed || 0}</p>
            <p className="text-gray-500 text-sm">Analysierte Dokumente</p>
          </div>
          <div className="bg-[#121212] border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-amber-400">{knowledge?.cases_count || 0}</p>
            <p className="text-gray-500 text-sm">Fälle</p>
          </div>
        </div>

        {/* Onboarding / Base Profile */}
        <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <User className="w-5 h-5 text-blue-400" /> Basisprofil
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setEditMode(!editMode)}
              className="text-gray-400"
              data-testid="edit-profile-btn"
            >
              <Edit className="w-4 h-4 mr-1" /> {editMode ? 'Abbrechen' : 'Bearbeiten'}
            </Button>
          </div>

          {editMode ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {onboardingFields.map(f => (
                  <div key={f.key}>
                    <Label className="text-gray-400 text-xs">{f.label}</Label>
                    <Input
                      value={onboarding[f.key] || ''}
                      onChange={(e) => setOnboarding({ ...onboarding, [f.key]: e.target.value })}
                      placeholder={f.placeholder}
                      className="mt-1 bg-black/30 border-white/10 text-white text-sm"
                      data-testid={`onboarding-${f.key}`}
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-end pt-2">
                <Button onClick={handleSaveOnboarding} disabled={saving} className="btn-primary" data-testid="save-profile-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                  Speichern
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {onboardingFields.map(f => {
                const val = onboarding[f.key];
                if (!val) return null;
                return (
                  <div key={f.key} className="flex gap-2 text-sm py-1">
                    <span className="text-gray-500 min-w-[140px]">{f.label}:</span>
                    <span className="text-white">{val}</span>
                  </div>
                );
              })}
              {!Object.values(onboarding).some(v => v) && (
                <p className="text-gray-500 text-sm col-span-2">
                  Noch kein Basisprofil angelegt. Klicken Sie auf "Bearbeiten" um Ihre Grunddaten einzugeben.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Learned Facts */}
        <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" /> Gelernte Fakten
            </h2>
            {facts.length > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setDeleteDialogOpen(true)} className="text-red-400 hover:bg-red-500/10 text-xs" data-testid="clear-memory-btn">
                <Trash2 className="w-3 h-3 mr-1" /> Alles löschen
              </Button>
            )}
          </div>

          {profile.summary && (
            <p className="text-gray-300 text-sm mb-4 bg-purple-500/5 border border-purple-500/10 rounded-lg p-3">{profile.summary}</p>
          )}

          {facts.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 text-sm">Die KI hat noch keine Fakten aus Gesprächen gelernt.</p>
              <p className="text-gray-600 text-xs mt-1">Starten Sie ein Gespräch im KI-Chat, damit die KI beginnt, sich Dinge zu merken.</p>
            </div>
          ) : (
            <div className="space-y-1 max-h-[400px] overflow-y-auto">
              {facts.map((fact, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center justify-between gap-2 px-3 py-2 bg-black/20 rounded text-sm group hover:bg-black/30"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="px-2 py-0.5 bg-purple-500/10 text-purple-300 rounded text-xs font-medium flex-shrink-0">
                      {fact.key}
                    </span>
                    <span className="text-gray-300 truncate">{fact.value}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-gray-600 text-xs hidden sm:inline">{fact.source}</span>
                    <button
                      onClick={() => handleDeleteFact(index)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity"
                      data-testid={`delete-fact-${index}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Documents Knowledge */}
        <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
          <button
            onClick={() => setShowDocs(!showDocs)}
            className="flex items-center justify-between w-full"
          >
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              Analysierte Dokumente ({knowledge?.documents_analyzed || 0})
            </h2>
            {showDocs ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </button>
          {showDocs && (
            <div className="mt-4 space-y-2 max-h-[400px] overflow-y-auto">
              {(knowledge?.documents || []).map((doc) => (
                <div key={doc.id} className="bg-black/20 rounded-lg p-3">
                  <p className="text-white text-sm font-medium">{doc.display_name}</p>
                  {doc.ai_summary && <p className="text-gray-400 text-xs mt-1 line-clamp-2">{doc.ai_summary}</p>}
                  <div className="flex items-center gap-2 mt-1">
                    {doc.document_type && <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded">{doc.document_type}</span>}
                    {doc.sender && <span className="text-xs text-gray-500">{doc.sender}</span>}
                  </div>
                </div>
              ))}
              {(knowledge?.documents || []).length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">Noch keine Dokumente analysiert</p>
              )}
            </div>
          )}
        </div>

        {/* Cases Knowledge */}
        <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
          <button
            onClick={() => setShowCases(!showCases)}
            className="flex items-center justify-between w-full"
          >
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-amber-400" />
              Bekannte Fälle ({knowledge?.cases_count || 0})
            </h2>
            {showCases ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </button>
          {showCases && (
            <div className="mt-4 space-y-2 max-h-[400px] overflow-y-auto">
              {(knowledge?.cases || []).map((c) => (
                <div key={c.id} className="bg-black/20 rounded-lg p-3">
                  <p className="text-white text-sm font-medium">{c.title}</p>
                  {c.description && <p className="text-gray-400 text-xs mt-1">{c.description}</p>}
                  <span className={`text-xs px-2 py-0.5 rounded mt-1 inline-block ${
                    c.status === 'open' ? 'bg-blue-500/10 text-blue-300' :
                    c.status === 'closed' ? 'bg-gray-500/10 text-gray-400' :
                    'bg-amber-500/10 text-amber-300'
                  }`}>{c.status}</span>
                </div>
              ))}
              {(knowledge?.cases || []).length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">Noch keine Fälle vorhanden</p>
              )}
            </div>
          )}
        </div>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="bg-[#1A1A1A] border-red-500/20 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-red-400 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5" />
                KI-Gedächtnis endgültig löschen
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 space-y-2">
                <p className="text-red-300 text-sm font-medium">
                  Diese Aktion kann nicht rückgängig gemacht werden!
                </p>
                <p className="text-gray-400 text-sm">
                  Folgende Daten werden unwiderruflich gelöscht:
                </p>
                <ul className="text-gray-400 text-sm list-disc pl-5 space-y-1">
                  <li><span className="text-white">{facts.length} gelernte Fakten</span> aus Gesprächen und Dokumenten</li>
                  <li>KI-Zusammenfassung Ihres Profils</li>
                  <li>Alle aus Konversationen extrahierten Informationen</li>
                </ul>
                <p className="text-amber-400 text-xs mt-2">
                  Ihr Basisprofil (Name, Adresse, etc.) bleibt erhalten und kann separat bearbeitet werden.
                </p>
              </div>

              <div>
                <Label className="text-gray-400 text-sm flex items-center gap-2">
                  <Lock className="w-3 h-3" /> Bestätigen Sie mit Ihrem Passwort
                </Label>
                <Input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder="Ihr Passwort eingeben"
                  className="mt-2 bg-black/30 border-white/10 text-white"
                  data-testid="delete-confirm-password"
                  onKeyDown={(e) => { if (e.key === 'Enter') handleClearMemory(); }}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="ghost" onClick={() => { setDeleteDialogOpen(false); setDeletePassword(''); }} className="text-gray-400">
                  Abbrechen
                </Button>
                <Button 
                  onClick={handleClearMemory} 
                  disabled={deleting || !deletePassword.trim()}
                  className="bg-red-600 hover:bg-red-700 text-white"
                  data-testid="confirm-delete-memory-btn"
                >
                  {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
                  Endgültig löschen
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
