import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, MapPin, Phone, Heart, Briefcase, ChevronRight, Shield, Check } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { aiAPI } from '../lib/api';
import { toast } from 'sonner';

const steps = [
  { id: 'personal', title: 'Persönliche Daten', icon: User, fields: ['full_name', 'birthdate', 'phone'] },
  { id: 'address', title: 'Adresse', icon: MapPin, fields: ['address'] },
  { id: 'family', title: 'Familie', icon: Heart, fields: ['marital_status', 'partner_name', 'children'] },
  { id: 'work', title: 'Beruf & Versicherung', icon: Briefcase, fields: ['employer', 'occupation', 'insurance_health'] },
];

const fieldConfig = {
  full_name: { label: 'Vollständiger Name', placeholder: 'Max Mustermann' },
  birthdate: { label: 'Geburtsdatum', placeholder: '01.01.1990' },
  phone: { label: 'Telefonnummer', placeholder: '+49 123 456789' },
  address: { label: 'Vollständige Adresse', placeholder: 'Musterstr. 1, 12345 Berlin' },
  marital_status: { label: 'Familienstand', placeholder: 'Verheiratet / Ledig / Geschieden' },
  partner_name: { label: 'Partner / Ehepartner', placeholder: 'Name des Partners (optional)' },
  children: { label: 'Kinder', placeholder: 'z.B. 2 Kinder (Lisa 5, Max 8) oder keine' },
  employer: { label: 'Arbeitgeber', placeholder: 'Firma GmbH' },
  occupation: { label: 'Beruf / Position', placeholder: 'z.B. Softwareentwickler' },
  insurance_health: { label: 'Krankenversicherung', placeholder: 'z.B. AOK, TK, Privat...' },
};

export default function OnboardingWizard({ onComplete }) {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [data, setData] = useState({});
  const [saving, setSaving] = useState(false);

  const currentStep = steps[step];
  const isLast = step === steps.length - 1;

  const handleNext = () => {
    if (isLast) {
      handleSave();
    } else {
      setStep(s => s + 1);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await aiAPI.saveOnboarding(data);
      toast.success('Profil gespeichert! Willkommen bei CaseDesk AI.');
      if (onComplete) onComplete();
      else navigate('/');
    } catch (error) {
      toast.error('Fehler beim Speichern');
    }
    setSaving(false);
  };

  const handleSkip = () => {
    if (onComplete) onComplete();
    else navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-4">
      <motion.div
        key={step}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-full max-w-lg"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-500/10 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-purple-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">Willkommen bei CaseDesk AI</h1>
          <p className="text-gray-500 text-sm mt-2">
            Damit Ihr KI-Assistent Sie von Anfang an besser unterstützen kann, benötigen wir einige Grundinformationen.
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-6">
          {steps.map((s, i) => (
            <div
              key={s.id}
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                i === step ? 'bg-purple-400' : i < step ? 'bg-purple-400/40' : 'bg-white/10'
              }`}
            />
          ))}
        </div>

        {/* Form */}
        <div className="bg-[#121212] border border-white/10 rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            {(() => { const Icon = currentStep.icon; return <Icon className="w-5 h-5 text-purple-400" />; })()}
            <h2 className="text-lg font-semibold text-white">{currentStep.title}</h2>
            <span className="text-gray-600 text-sm ml-auto">{step + 1}/{steps.length}</span>
          </div>

          <div className="space-y-4">
            {currentStep.fields.map(field => {
              const cfg = fieldConfig[field];
              return (
                <div key={field}>
                  <Label className="text-gray-400 text-sm">{cfg.label}</Label>
                  <Input
                    value={data[field] || ''}
                    onChange={(e) => setData({ ...data, [field]: e.target.value })}
                    placeholder={cfg.placeholder}
                    className="mt-1 bg-black/30 border-white/10 text-white"
                    data-testid={`onboarding-${field}`}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-8">
            <div className="flex gap-2">
              {step > 0 && (
                <Button variant="ghost" onClick={() => setStep(s => s - 1)} className="text-gray-400">
                  Zurück
                </Button>
              )}
              <Button variant="ghost" onClick={handleSkip} className="text-gray-600 text-sm">
                Überspringen
              </Button>
            </div>
            <Button onClick={handleNext} disabled={saving} className="btn-primary" data-testid="onboarding-next-btn">
              {saving ? 'Wird gespeichert...' : isLast ? (
                <><Check className="w-4 h-4 mr-2" /> Fertig</>
              ) : (
                <><ChevronRight className="w-4 h-4 mr-2" /> Weiter</>
              )}
            </Button>
          </div>
        </div>

        <p className="text-center text-gray-600 text-xs mt-6">
          Alle Daten bleiben lokal auf Ihrem Server. Sie können diese jederzeit unter "KI-Wissen" ändern.
        </p>
      </motion.div>
    </div>
  );
}
