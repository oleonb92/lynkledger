import axios from 'axios';
import { store } from '../../store';
import { logout } from '../../store/slices/authSlice';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de solicitud para agregar el token
api.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de respuesta para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Manejar error 401 (No autorizado)
      if (error.response.status === 401) {
        store.dispatch(logout());
      }
      
      // Personalizar mensajes de error
      const message = error.response.data.message || error.response.data.detail || 'Ha ocurrido un error';
      return Promise.reject(new Error(message));
    }
    
    return Promise.reject(error);
  }
);

export default api; 