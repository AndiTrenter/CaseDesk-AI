import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Lock, Mail } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await login(email, password);
      toast.success(t('auth.login') + ' ' + t('common.success').toLowerCase());
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || t('auth.loginError'));
    }
    
    setIsLoading(false);
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
            Secure document and case management with AI assistance
          </p>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div 
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Logo for mobile */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">CaseDesk AI</h1>
          </div>

          <div className="bg-[#121212] border border-white/5 rounded-xl p-8">
            <div className="text-center mb-8">
              <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-white">{t('auth.login')}</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <Label className="text-gray-300">{t('auth.email')}</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-black/30 border-white/10 text-white"
                    placeholder="admin@example.com"
                    required
                    data-testid="login-email-input"
                  />
                </div>
              </div>

              <div>
                <Label className="text-gray-300">{t('auth.password')}</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 bg-black/30 border-white/10 text-white"
                    placeholder="••••••••"
                    required
                    data-testid="login-password-input"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full btn-primary"
                disabled={isLoading}
                data-testid="login-submit-btn"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    {t('common.loading')}
                  </span>
                ) : (
                  t('auth.loginButton')
                )}
              </Button>
            </form>
          </div>

          <p className="text-center text-gray-600 text-sm mt-6">
            CaseDesk AI v1.0.0 - Self-Hosted
          </p>
        </motion.div>
      </div>
    </div>
  );
}
