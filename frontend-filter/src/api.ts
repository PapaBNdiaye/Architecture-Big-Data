import axios from 'axios';
import type { RunPayload, TaskStatus, Row } from './types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
});

// Intercepteur pour gérer les erreurs globalement
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Lancer une requête batch
  async runQuery(payload: RunPayload): Promise<{ task_id: string }> {
    const response = await api.post('/run', payload);
    return response.data;
  },

  // Vérifier le statut d'une tâche
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await api.get(`/status/${taskId}`);
    return response.data;
  },

  // Récupérer les résultats d'une tâche
  async fetchResults(taskId: string): Promise<{ data: Row[] }> {
    const response = await api.get(`/fetch/${taskId}`);
    return response.data;
  },
};

export default api;