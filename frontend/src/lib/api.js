import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('casedesk_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('casedesk_token');
      localStorage.removeItem('casedesk_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  login: (email, password) => {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  validateInvitation: (token) => api.get(`/auth/invitation/${token}`),
  registerWithInvitation: (token, data) => {
    const formData = new FormData();
    formData.append('full_name', data.full_name);
    formData.append('password', data.password);
    return api.post(`/auth/register/${token}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Users (Admin)
export const usersAPI = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  delete: (id) => api.delete(`/users/${id}`),
  invite: (email, role = 'user') => {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('role', role);
    return api.post('/users/invite', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  listInvitations: () => api.get('/users/invitations'),
  cancelInvitation: (id) => api.delete(`/users/invitations/${id}`),
};

// Setup
export const setupAPI = {
  getStatus: () => api.get('/setup/status'),
  init: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    });
    return api.post('/setup/init', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Cases
export const casesAPI = {
  list: (params) => api.get('/cases', { params }),
  get: (id) => api.get(`/cases/${id}`),
  create: (data) => api.post('/cases', data),
  update: (id, data) => api.put(`/cases/${id}`, data),
  delete: (id) => api.delete(`/cases/${id}`),
};

// Documents
export const documentsAPI = {
  list: (params) => api.get('/documents', { params }),
  get: (id) => api.get(`/documents/${id}`),
  upload: (file, caseId, documentType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_process', 'true');
    if (caseId) formData.append('case_id', caseId);
    if (documentType) formData.append('document_type', documentType);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000 // 2 minutes for OCR + AI processing
    });
  },
  ocr: (id) => api.post(`/documents/${id}/ocr`),
  reprocess: (id) => api.post(`/documents/${id}/reprocess`, {}, { timeout: 120000 }),
  delete: (id) => api.delete(`/documents/${id}`),
};

// Tasks
export const tasksAPI = {
  list: (params) => api.get('/tasks', { params }),
  create: (data) => api.post('/tasks', data),
  update: (id, data) => api.put(`/tasks/${id}`, data),
  delete: (id) => api.delete(`/tasks/${id}`),
};

// Events
export const eventsAPI = {
  list: (params) => api.get('/events', { params }),
  create: (data) => api.post('/events', data),
  update: (id, data) => api.put(`/events/${id}`, data),
  delete: (id) => api.delete(`/events/${id}`),
};

// Drafts
export const draftsAPI = {
  list: (params) => api.get('/drafts', { params }),
  create: (data) => api.post('/drafts', data),
  update: (id, data) => api.put(`/drafts/${id}`, data),
  delete: (id) => api.delete(`/drafts/${id}`),
};

// AI
export const aiAPI = {
  chat: (message, sessionId, caseId) => {
    const formData = new FormData();
    formData.append('message', message);
    if (sessionId) formData.append('session_id', sessionId);
    if (caseId) formData.append('case_id', caseId);
    return api.post('/ai/chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  history: (sessionId) => api.get('/ai/history', { params: { session_id: sessionId } }),
};

// Settings
export const settingsAPI = {
  getSystem: () => api.get('/settings/system'),
  updateSystem: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    });
    return api.put('/settings/system', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getUser: () => api.get('/settings/user'),
  updateUser: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    });
    return api.put('/settings/user', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Mail
export const mailAPI = {
  listAccounts: () => api.get('/mail/accounts'),
  createAccount: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => formData.append(key, data[key]));
    return api.post('/mail/accounts', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  deleteAccount: (id) => api.delete(`/mail/accounts/${id}`),
};

// Emails
export const emailsAPI = {
  list: (params) => api.get('/emails', { params }),
  get: (id) => api.get(`/emails/${id}`),
  fetch: (accountId) => api.post(`/emails/fetch/${accountId}`),
  process: (id) => api.post(`/emails/${id}/process`),
  link: (id, caseId) => {
    const formData = new FormData();
    formData.append('case_id', caseId);
    return api.post(`/emails/${id}/link`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  importAttachment: (emailId, attachmentId, caseId) => {
    const formData = new FormData();
    if (caseId) formData.append('case_id', caseId);
    return api.post(`/emails/${emailId}/import-attachment/${attachmentId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  delete: (id) => api.delete(`/emails/${id}`),
};

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};

// Export
export const exportAPI = {
  all: () => api.get('/export/all'),
  case: (caseId) => api.get(`/export/case/${caseId}`),
};

// Correspondence
export const correspondenceAPI = {
  list: (caseId) => api.get('/correspondence', { params: caseId ? { case_id: caseId } : {} }),
  get: (id) => api.get(`/correspondence/${id}`),
  update: (id, data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        formData.append(key, data[key]);
      }
    });
    return api.put(`/correspondence/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  delete: (id) => api.delete(`/correspondence/${id}`),
  download: (id) => api.get(`/correspondence/${id}/download`, { responseType: 'blob' }),
  send: (id, mailAccountId, recipientEmail) => {
    const formData = new FormData();
    formData.append('mail_account_id', mailAccountId);
    formData.append('recipient_email', recipientEmail);
    return api.post(`/correspondence/${id}/send`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Extended Cases API
export const caseResponseAPI = {
  analyze: (caseId) => api.get(`/cases/${caseId}/analyze`, { timeout: 120000 }),
  generateResponse: (caseId, data) => {
    const formData = new FormData();
    formData.append('response_type', data.response_type);
    formData.append('recipient', data.recipient);
    formData.append('subject', data.subject);
    if (data.instructions) formData.append('instructions', data.instructions);
    if (data.document_ids) formData.append('document_ids', JSON.stringify(data.document_ids));
    if (data.output_format) formData.append('output_format', data.output_format);
    return api.post(`/cases/${caseId}/generate-response`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000
    });
  },
  getHistory: (caseId) => api.get(`/cases/${caseId}/history`),
  getDocuments: (caseId) => api.get(`/cases/${caseId}/documents`),
};

// Extended Documents API
export const documentUpdateAPI = {
  update: (id, data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (data[key] !== null && data[key] !== undefined) {
        if (key === 'tags') {
          formData.append(key, JSON.stringify(data[key]));
        } else {
          formData.append(key, data[key]);
        }
      }
    });
    return api.put(`/documents/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  preview: (id) => api.get(`/documents/${id}/preview`),
  downloadUrl: (id) => `${API_URL}/api/documents/${id}/download`,
};

// Health
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
