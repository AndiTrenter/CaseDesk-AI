import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, Database, Cloud, HardDrive, Mail, Bot, 
  CheckCircle, XCircle, AlertTriangle, RefreshCw, Server
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { healthAPI } from '../lib/api';
import { toast } from 'sonner';

const StatusIcon = ({ status }) => {
  if (status === 'connected' || status === 'ok' || status === 'configured' || status === 'installed' || status === 'active')
    return <CheckCircle className="w-5 h-5 text-emerald-400" />;
  if (status === 'unavailable' || status === 'no_api_key' || status === 'not_installed' || status === 'no_accounts' || status === 'disabled')
    return <AlertTriangle className="w-5 h-5 text-amber-400" />;
  return <XCircle className="w-5 h-5 text-red-400" />;
};

const statusColor = (status) => {
  if (status === 'connected' || status === 'ok' || status === 'configured' || status === 'installed' || status === 'active')
    return 'border-emerald-500/20 bg-emerald-500/5';
  if (status === 'unavailable' || status === 'no_api_key' || status === 'not_installed' || status === 'no_accounts' || status === 'disabled')
    return 'border-amber-500/20 bg-amber-500/5';
  return 'border-red-500/20 bg-red-500/5';
};

const serviceIcon = (name) => {
  const icons = { mongodb: Database, openai: Cloud, ollama: Bot, ocr: Server, email_sync: Mail, storage: HardDrive, tesseract: Server, ai: Bot };
  return icons[name] || Activity;
};

const serviceName = (name) => {
  const names = { mongodb: 'MongoDB', openai: 'OpenAI API', ollama: 'Ollama (Lokal)', ocr: 'OCR Service', email_sync: 'E-Mail Sync', storage: 'Speicher', tesseract: 'Tesseract OCR', ai: 'KI-Provider' };
  return names[name] || name;
};

export default function HealthDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadHealth(); }, []);

  const loadHealth = async () => {
    setLoading(true);
    try {
      const response = await healthAPI.adminHealth();
      setData(response.data);
    } catch (error) {
      toast.error('Healthcheck fehlgeschlagen');
    }
    setLoading(false);
  };

  return (
    <div className="page-container" data-testid="health-dashboard">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                <Activity className="w-5 h-5 text-emerald-400" />
              </div>
              System-Status
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              {data?.timestamp ? `Zuletzt geprüft: ${new Date(data.timestamp).toLocaleString('de-DE')}` : 'Wird geladen...'}
            </p>
          </div>
          <Button onClick={loadHealth} disabled={loading} className="btn-secondary" data-testid="refresh-health-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Aktualisieren
          </Button>
        </div>

        {loading && !data ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
          </div>
        ) : data?.services ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.services).map(([name, info], index) => {
              const Icon = serviceIcon(name);
              return (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`border rounded-xl p-5 ${statusColor(info.status)}`}
                  data-testid={`health-${name}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5 text-gray-400" />
                      <h3 className="text-white font-medium">{serviceName(name)}</h3>
                    </div>
                    <StatusIcon status={info.status} />
                  </div>

                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Status:</span>
                      <span className={`font-medium ${
                        info.status === 'connected' || info.status === 'ok' || info.status === 'configured' || info.status === 'installed' || info.status === 'active'
                          ? 'text-emerald-400'
                          : info.status === 'error' ? 'text-red-400' : 'text-amber-400'
                      }`}>
                        {info.status}
                      </span>
                    </div>

                    {/* MongoDB specifics */}
                    {info.documents !== undefined && (
                      <div className="text-gray-400">Dokumente: {info.documents} | Benutzer: {info.users}</div>
                    )}

                    {/* Storage specifics */}
                    {info.total_gb !== undefined && (
                      <>
                        <div className="text-gray-400">{info.used_gb} GB / {info.total_gb} GB ({info.usage_percent}%)</div>
                        <div className="w-full bg-black/30 rounded-full h-2 mt-2">
                          <div
                            className={`h-2 rounded-full ${info.usage_percent > 90 ? 'bg-red-500' : info.usage_percent > 70 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                            style={{ width: `${Math.min(info.usage_percent, 100)}%` }}
                          />
                        </div>
                      </>
                    )}

                    {/* Ollama models */}
                    {info.models && info.models.length > 0 && (
                      <div className="text-gray-400">Modelle: {info.models.join(', ')}</div>
                    )}

                    {/* Notes */}
                    {info.note && <div className="text-gray-500 text-xs mt-1">{info.note}</div>}
                    {info.version && <div className="text-gray-500 text-xs">{info.version}</div>}
                    {info.url && <div className="text-gray-500 text-xs">{info.url}</div>}
                    {info.accounts !== undefined && <div className="text-gray-400">Konten: {info.accounts}</div>}
                    {info.error && <div className="text-red-400 text-xs">{info.error}</div>}
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-20 text-gray-500">Keine Daten verfügbar</div>
        )}
      </div>
    </div>
  );
}
