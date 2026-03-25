import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Shield, Loader2, AlertCircle, CheckCircle, User, Lock, Mail } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { authAPI } from '../lib/api';
import { toast } from 'sonner';

export default function Register() {
  const { t } = useTranslation();
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [invitation, setInvitation] = useState(null);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    full_name: '',
    password: '',
    confirmPassword: ''
  });

  useEffect(() => {
    validateInvitation();
  }, [token]);

  const validateInvitation = async () => {
    try {
      const response = await authAPI.validateInvitation(token);
      if (response.data.valid) {
        setInvitation(response.data);
      } else {
        setError(response.data.error || 'Einladung ungültig oder abgelaufen');
      }
    } catch (err) {
      setError('Einladung konnte nicht überprüft werden');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwörter stimmen nicht überein');
      return;
    }
    
    if (formData.password.length < 6) {
      toast.error('Passwort muss mindestens 6 Zeichen lang sein');
      return;
    }
    
    setSubmitting(true);
    
    try {
      const response = await authAPI.registerWithInvitation(token, {
        full_name: formData.full_name,
        password: formData.password
      });
      
      if (response.data.success) {
        toast.success('Konto erfolgreich erstellt!');
        // Save token and redirect to onboarding
        if (response.data.access_token) {
          localStorage.setItem('casedesk_token', response.data.access_token);
          localStorage.setItem('casedesk_user', JSON.stringify(response.data.user));
          navigate('/onboarding');
        } else {
          navigate('/login');
        }
      } else {
        toast.error(response.data.error || 'Registrierung fehlgeschlagen');
      }
    } catch (err) {
      toast.error('Registrierung fehlgeschlagen');
    }
    
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-white animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Einladung wird überprüft...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md bg-[#121212] border border-white/10 rounded-2xl p-8 text-center"
        >
          <div className="w-16 h-16 bg-red-500/10 rounded-xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <h1 className="text-xl font-bold text-white mb-2">Einladung ungültig</h1>
          <p className="text-gray-400 mb-6">{error}</p>
          <Button onClick={() => navigate('/login')} className="btn-secondary">
            Zur Anmeldung
          </Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-500/10 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">CaseDesk AI</h1>
          <p className="text-gray-500 text-sm mt-1">Konto erstellen</p>
        </div>

        {/* Invitation Info */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
            <div>
              <p className="text-white text-sm font-medium">Einladung gültig</p>
              <p className="text-gray-400 text-xs">
                Eingeladen von {invitation?.invited_by} für {invitation?.email}
              </p>
            </div>
          </div>
        </div>

        {/* Register Form */}
        <div className="bg-[#121212] border border-white/10 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label className="text-gray-400">E-Mail</Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="email"
                  value={invitation?.email || ''}
                  disabled
                  className="pl-10 bg-black/30 border-white/10 text-gray-400"
                />
              </div>
            </div>
            
            <div>
              <Label className="text-gray-400">Vollständiger Name</Label>
              <div className="relative mt-1">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="pl-10 bg-black/30 border-white/10 text-white"
                  placeholder="Max Mustermann"
                  required
                />
              </div>
            </div>

            <div>
              <Label className="text-gray-400">Passwort</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 bg-black/30 border-white/10 text-white"
                  placeholder="Mindestens 6 Zeichen"
                  required
                  minLength={6}
                />
              </div>
            </div>

            <div>
              <Label className="text-gray-400">Passwort bestätigen</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <Input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="pl-10 bg-black/30 border-white/10 text-white"
                  placeholder="Passwort wiederholen"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full btn-primary"
              data-testid="register-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Wird erstellt...
                </>
              ) : (
                'Konto erstellen'
              )}
            </Button>
          </form>
        </div>

        <p className="text-center text-gray-600 text-xs mt-6">
          Bereits ein Konto?{' '}
          <button 
            onClick={() => navigate('/login')}
            className="text-blue-400 hover:underline"
          >
            Anmelden
          </button>
        </p>
      </motion.div>
    </div>
  );
}
