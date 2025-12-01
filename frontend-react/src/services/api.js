import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_URL,
    timeout: 600000, // 10 minutes for long processing
});

export const fetchServerState = async () => {
    const response = await api.get('/state');
    return response.data;
};

export const fetchDbStatus = async () => {
    const response = await api.get('/db-status');
    return response.data;
};

export const clearDb = async () => {
    const response = await api.post('/clear-db');
    return response.data;
};

export const screenResumes = async (formData) => {
    const response = await api.post('/screen', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const compareCandidates = async (candidate1, candidate2) => {
    const response = await api.post('/compare', {
        candidate1_name: candidate1,
        candidate2_name: candidate2,
    });
    return response.data;
};

export const fetchScreeningStatus = async (sessionId) => {
    const response = await api.get(`/screen/${sessionId}/status`);
    return response.data;
};

export const fetchHistory = async () => {
    const response = await api.get('/history');
    return response.data;
};

export const exportSession = async (sessionId) => {
    const response = await api.get(`/export/${sessionId}`, {
        responseType: 'blob',
    });
    return response.data;
};

export const getResumeUrl = (filename) => {
    return `${API_URL}/resumes/${encodeURIComponent(filename)}`;
};

export default api;
