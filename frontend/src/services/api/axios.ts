import axios from 'axios';
import { store } from '../../store';
import { logout } from '../../store/slices/authSlice';

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('Request:', {
      url: config.url,
      method: config.method,
      data: config.data,
      headers: config.headers,
      baseURL: config.baseURL
    });
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('Response:', {
      status: response.status,
      statusText: response.statusText,
      data: response.data,
      headers: response.headers
    });
    return response;
  },
  async (error) => {
    if (error.response) {
      // La petición fue hecha y el servidor respondió con un código de estado
      // que está fuera del rango 2xx
      console.error('Response error details:', {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
        headers: error.response.headers,
        config: {
          url: error.config.url,
          method: error.config.method,
          data: error.config.data,
          headers: error.config.headers
        }
      });
    } else if (error.request) {
      // La petición fue hecha pero no se recibió respuesta
      console.error('No response received:', error.request);
    } else {
      // Algo ocurrió al configurar la petición que disparó un error
      console.error('Request setup error:', error.message);
    }

    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const res = await axios.post(`${BASE_URL}/token/refresh/`, { refresh: refreshToken });
          const { access } = res.data;
          localStorage.setItem('token', access);
          originalRequest.headers['Authorization'] = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshError) {
          console.error('Token refresh error:', refreshError);
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          store.dispatch(logout());
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api; 