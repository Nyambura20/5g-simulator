import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const baseStationAPI = {
  getAll: () => api.get('/base-stations/'),
  create: (data) => api.post('/base-stations/', data),
  update: (id, data) => api.put(`/base-stations/${id}/`, data),
  delete: (id) => api.delete(`/base-stations/${id}/`),
};

export const simulationAPI = {
  create: (data) => api.post('/simulations/', data),
  run: (id) => api.post(`/simulations/${id}/run/`),
  getHeatmap: (id) => api.get(`/simulations/${id}/heatmap_data/`),
  getAll: () => api.get('/simulations/'),
  getOne: (id) => api.get(`/simulations/${id}/`),
};

export const buildingAPI = {
  getAll: () => api.get('/buildings/'),
  withinBounds: (bounds) => api.get('/buildings/within_bounds/', { params: bounds }),
};

export default api;