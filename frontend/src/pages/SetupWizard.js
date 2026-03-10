import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Globe, User, Brain, Shield, Rocket } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { setupAPI } from '../lib/api';
import { toast } from 'sonner';

const STEPS = [
  { id: 'language', icon: Globe },
  { id: 'admin', icon: User },
  { id: 'ai', icon: Brain },
  { id: 'privacy', icon: Shield },
  { id: 'complete', icon: Rocket }
];

export default function SetupWizard({ onComplete }) {
  const { t, i18n } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    language: 'en',
    admin_email: '',
    admin_username: '',
    admin_password: '',
    admin_password_confirm: '',
    admin_full_name: '',
    ai_provider: 'ollama',
    openai_api_key: '',
    internet_access: 'denied'
  });

  const handleLanguageChange = (lang) => {
    setFormData({ ...formData, language: lang });
    i18n.changeLanguage(lang);
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const validateStep = () => {
    switch (currentStep) {
      case 0: // Language
        return true;
      case 1: // Admin
        if (!formData.admin_email || !formData.admin_username || !formData.admin_password) {
          toast.error('Please fill in all required fields');
          return false;
        }
        if (formData.admin_password !== formData.admin_password_confirm) {
          toast.error('Passwords do not match');
          return false;
        }
        if (formData.admin_password.length < 6) {
          toast.error('Password must be at least 6 characters');
          return false;
        }
        return true;
      case 2: // AI
        if (formData.ai_provider === 'openai' && !formData.openai_api_key) {
          toast.error('Please enter your OpenAI API key');
          return false;
        }
        return true;
      case 3: // Privacy
        return true;
      default:
        return true;
    }
  };

  const nextStep = () => {
    if (validateStep()) {
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const completeSetup = async () => {
    setIsSubmitting(true);
    try {
      const response = await setupAPI.init({
        language: formData.language,
        admin_email: formData.admin_email,
        admin_username: formData.admin_username,
        admin_password: formData.admin_password,
        admin_full_name: formData.admin_full_name || null,
        ai_provider: formData.ai_provider,
        openai_api_key: formData.ai_provider === 'openai' ? formData.openai_api_key : null,
        internet_access: formData.internet_access
      });

      if (response.data.success) {
        localStorage.setItem('casedesk_token', response.data.access_token);
        localStorage.setItem('casedesk_user', JSON.stringify(response.data.user));
        toast.success(t('setup.completeTitle'));
        onComplete();
      }
    } catch (error) {
      console.error('Setup error:', error);
      toast.error(error.response?.data?.detail || 'Setup failed');
    }
    setIsSubmitting(false);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return <LanguageStep formData={formData} onChange={handleLanguageChange} t={t} />;
      case 1:
        return <AdminStep formData={formData} onChange={handleChange} t={t} />;
      case 2:
        return <AIStep formData={formData} onChange={handleChange} t={t} />;
      case 3:
        return <PrivacyStep formData={formData} onChange={handleChange} t={t} />;
      case 4:
        return <CompleteStep t={t} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex">
      {/* Left Side - Background */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1772050138768-2107c6e62a03?crop=entropy&cs=srgb&fm=jpg&q=85)',
            filter: 'brightness(0.4)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0A0A0A] via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col justify-center px-12">
          <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">CaseDesk AI</h1>
          <p className="text-xl text-gray-300 max-w-md">
            {t('setup.subtitle')}
          </p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Logo for mobile */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">CaseDesk AI</h1>
            <p className="text-gray-400">{t('setup.subtitle')}</p>
          </div>

          {/* Progress Steps */}
          <div className="flex justify-between mb-8">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;
              
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div className={`
                    w-10 h-10 rounded-full flex items-center justify-center transition-all
                    ${isCompleted ? 'bg-green-500/20 text-green-400' : ''}
                    ${isActive ? 'bg-white/10 text-white ring-2 ring-white/20' : ''}
                    ${!isActive && !isCompleted ? 'bg-white/5 text-gray-600' : ''}
                  `}>
                    {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span className="text-xs mt-2 text-gray-500">
                    {t(`setup.step`)} {index + 1}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Step Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="bg-[#121212] border border-white/5 rounded-xl p-6"
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-6">
            <Button
              variant="ghost"
              onClick={prevStep}
              disabled={currentStep === 0}
              className="text-gray-400 hover:text-white"
              data-testid="setup-back-btn"
            >
              {t('setup.back')}
            </Button>
            
            {currentStep < STEPS.length - 1 ? (
              <Button
                onClick={nextStep}
                className="btn-primary"
                data-testid="setup-continue-btn"
              >
                {t('setup.continue')}
              </Button>
            ) : (
              <Button
                onClick={completeSetup}
                disabled={isSubmitting}
                className="btn-primary"
                data-testid="setup-finish-btn"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    {t('common.loading')}
                  </span>
                ) : (
                  t('setup.startUsing')
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Step Components
const LanguageStep = ({ formData, onChange, t }) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold text-white mb-2">{t('setup.languageTitle')}</h2>
      <p className="text-gray-400 text-sm">{t('setup.languageDesc')}</p>
    </div>
    
    <div className="grid grid-cols-2 gap-4">
      {[
        { code: 'en', name: 'English', flag: '🇬🇧' },
        { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
      ].map((lang) => (
        <button
          key={lang.code}
          onClick={() => onChange(lang.code)}
          className={`
            p-4 rounded-lg border transition-all text-left
            ${formData.language === lang.code 
              ? 'border-white/30 bg-white/5' 
              : 'border-white/10 hover:border-white/20'}
          `}
          data-testid={`lang-${lang.code}-btn`}
        >
          <span className="text-2xl mb-2 block">{lang.flag}</span>
          <span className="text-white font-medium">{lang.name}</span>
        </button>
      ))}
    </div>
  </div>
);

const AdminStep = ({ formData, onChange, t }) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold text-white mb-2">{t('setup.adminTitle')}</h2>
      <p className="text-gray-400 text-sm">{t('setup.adminDesc')}</p>
    </div>
    
    <div className="space-y-4">
      <div>
        <Label className="text-gray-300">{t('setup.email')} *</Label>
        <Input
          type="email"
          value={formData.admin_email}
          onChange={(e) => onChange('admin_email', e.target.value)}
          className="mt-1 bg-black/30 border-white/10 text-white"
          placeholder="admin@example.com"
          data-testid="admin-email-input"
        />
      </div>
      
      <div>
        <Label className="text-gray-300">{t('setup.username')} *</Label>
        <Input
          type="text"
          value={formData.admin_username}
          onChange={(e) => onChange('admin_username', e.target.value)}
          className="mt-1 bg-black/30 border-white/10 text-white"
          placeholder="admin"
          data-testid="admin-username-input"
        />
      </div>
      
      <div>
        <Label className="text-gray-300">{t('setup.fullName')}</Label>
        <Input
          type="text"
          value={formData.admin_full_name}
          onChange={(e) => onChange('admin_full_name', e.target.value)}
          className="mt-1 bg-black/30 border-white/10 text-white"
          placeholder="John Doe"
          data-testid="admin-fullname-input"
        />
      </div>
      
      <div>
        <Label className="text-gray-300">{t('setup.password')} *</Label>
        <Input
          type="password"
          value={formData.admin_password}
          onChange={(e) => onChange('admin_password', e.target.value)}
          className="mt-1 bg-black/30 border-white/10 text-white"
          placeholder="••••••••"
          data-testid="admin-password-input"
        />
      </div>
      
      <div>
        <Label className="text-gray-300">{t('setup.confirmPassword')} *</Label>
        <Input
          type="password"
          value={formData.admin_password_confirm}
          onChange={(e) => onChange('admin_password_confirm', e.target.value)}
          className="mt-1 bg-black/30 border-white/10 text-white"
          placeholder="••••••••"
          data-testid="admin-password-confirm-input"
        />
      </div>
    </div>
  </div>
);

const AIStep = ({ formData, onChange, t }) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold text-white mb-2">{t('setup.aiTitle')}</h2>
      <p className="text-gray-400 text-sm">{t('setup.aiDesc')}</p>
    </div>
    
    <div className="space-y-4">
      <div>
        <Label className="text-gray-300">{t('setup.aiProvider')}</Label>
        <div className="grid grid-cols-1 gap-3 mt-2">
          {[
            { id: 'ollama', label: 'Ollama (Lokal)', desc: 'Komplett lokal, kein Internet erforderlich', recommended: true },
            { id: 'openai', label: t('setup.aiOpenai'), desc: 'Benötigt API-Key und Internetzugriff' },
            { id: 'disabled', label: t('setup.aiDisabled'), desc: 'KI-Funktionen deaktiviert' }
          ].map((option) => (
            <button
              key={option.id}
              onClick={() => onChange('ai_provider', option.id)}
              className={`
                p-4 rounded-lg border transition-all text-left relative
                ${formData.ai_provider === option.id 
                  ? 'border-white/30 bg-white/5' 
                  : 'border-white/10 hover:border-white/20'}
              `}
              data-testid={`ai-provider-${option.id}-btn`}
            >
              {option.recommended && (
                <span className="absolute top-2 right-2 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
                  Empfohlen
                </span>
              )}
              <span className="text-white font-medium block">{option.label}</span>
              <span className="text-gray-500 text-sm">{option.desc}</span>
            </button>
          ))}
        </div>
      </div>
      
      {formData.ai_provider === 'ollama' && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <p className="text-green-300 text-sm">
            Ollama wird automatisch mit Docker installiert. Das Llama 3.2 Modell wird beim ersten Start heruntergeladen (ca. 2GB).
          </p>
        </div>
      )}
        <div>
          <Label className="text-gray-300">{t('setup.apiKey')}</Label>
          <Input
            type="password"
            value={formData.openai_api_key}
            onChange={(e) => onChange('openai_api_key', e.target.value)}
            className="mt-1 bg-black/30 border-white/10 text-white"
            placeholder={t('setup.apiKeyPlaceholder')}
            data-testid="openai-key-input"
          />
        </div>
      )}
    </div>
  </div>
);

const PrivacyStep = ({ formData, onChange, t }) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-semibold text-white mb-2">{t('setup.privacyTitle')}</h2>
      <p className="text-gray-400 text-sm">{t('setup.privacyDesc')}</p>
    </div>
    
    <div className="space-y-4">
      <div>
        <Label className="text-gray-300">{t('setup.internetAccess')}</Label>
        <div className="grid grid-cols-1 gap-3 mt-2">
          {[
            { id: 'denied', label: t('setup.internetDenied'), icon: Shield },
            { id: 'allowed', label: t('setup.internetAllowed'), icon: Globe }
          ].map((option) => {
            const Icon = option.icon;
            return (
              <button
                key={option.id}
                onClick={() => onChange('internet_access', option.id)}
                className={`
                  p-4 rounded-lg border transition-all text-left flex items-center gap-3
                  ${formData.internet_access === option.id 
                    ? 'border-white/30 bg-white/5' 
                    : 'border-white/10 hover:border-white/20'}
                `}
                data-testid={`internet-${option.id}-btn`}
              >
                <Icon className={`w-5 h-5 ${option.id === 'denied' ? 'text-green-400' : 'text-yellow-400'}`} />
                <span className="text-white font-medium">{option.label}</span>
              </button>
            );
          })}
        </div>
      </div>
      
      <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <p className="text-blue-300 text-sm">{t('setup.privacyNote')}</p>
      </div>
    </div>
  </div>
);

const CompleteStep = ({ t }) => (
  <div className="text-center py-8">
    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
      <Check className="w-8 h-8 text-green-400" />
    </div>
    <h2 className="text-2xl font-semibold text-white mb-2">{t('setup.completeTitle')}</h2>
    <p className="text-gray-400">{t('setup.completeDesc')}</p>
  </div>
);
