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

// Users
export const usersAPI = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  delete: (id) => api.delete(`/users/${id}`),
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

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};

// Health
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
