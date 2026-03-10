import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  FileText, Upload, Search, Filter, Trash2, 
  Eye, FileImage, File, MoreVertical 
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { documentsAPI } from '../lib/api';
import { toast } from 'sonner';

const DOC_TYPES = [
  { id: 'letter', label: 'Letter' },
  { id: 'invoice', label: 'Invoice' },
  { id: 'contract', label: 'Contract' },
  { id: 'form', label: 'Form' },
  { id: 'receipt', label: 'Receipt' },
  { id: 'other', label: 'Other' }
];

export default function Documents() {
  const { t } = useTranslation();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.list();
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load documents');
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    
    for (const file of files) {
      try {
        await documentsAPI.upload(file, null, 'other');
        toast.success(`${file.name} uploaded`);
      } catch (error) {
        console.error('Upload error:', error);
        toast.error(`Failed to upload ${file.name}`);
      }
    }
    
    setUploading(false);
    loadDocuments();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (id) => {
    try {
      await documentsAPI.delete(id);
      toast.success('Document deleted');
      loadDocuments();
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  const handleOCR = async (id) => {
    try {
      toast.info('Processing OCR...');
      await documentsAPI.ocr(id);
      toast.success('OCR completed');
      loadDocuments();
    } catch (error) {
      toast.error('OCR processing failed');
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getFileIcon = (mimeType) => {
    if (mimeType?.startsWith('image/')) return FileImage;
    return File;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="page-container" data-testid="documents-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('documents.title')}</h1>
          <p className="text-gray-400 text-sm">{documents.length} {t('documents.title').toLowerCase()}</p>
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
            <Upload className="w-4 h-4" />
            {uploading ? t('documents.processing') : t('documents.upload')}
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder={t('documents.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-[#121212] border-white/10 text-white"
            data-testid="search-documents-input"
          />
        </div>
      </div>

      {/* Documents Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">{t('documents.noDocuments')}</h3>
          <p className="text-gray-500">{t('documents.uploadFirst')}</p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredDocuments.map((doc, index) => {
            const FileIcon = getFileIcon(doc.mime_type);
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-[#121212] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors group"
                data-testid={`document-card-${index}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center">
                    <FileIcon className="w-5 h-5 text-gray-400" />
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical className="w-4 h-4 text-gray-400" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                      <DropdownMenuItem 
                        onClick={() => handleOCR(doc.id)}
                        className="text-gray-300 focus:bg-white/10"
                      >
                        <Eye className="w-4 h-4 mr-2" /> {t('documents.ocr')}
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => handleDelete(doc.id)}
                        className="text-red-400 focus:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> {t('documents.delete')}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <h3 className="text-white font-medium text-sm truncate mb-1">{doc.original_filename}</h3>
                <div className="flex items-center gap-2 text-gray-500 text-xs">
                  <span className="capitalize">{doc.document_type}</span>
                  <span>•</span>
                  <span>{formatFileSize(doc.size)}</span>
                </div>
                
                {doc.ocr_processed && (
                  <span className="inline-block mt-2 px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded">
                    OCR ✓
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
