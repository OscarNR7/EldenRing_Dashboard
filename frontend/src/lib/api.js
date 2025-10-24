import axios from 'axios';

// Lee la variable de entorno para la URL base de la API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Crea una instancia de Axios configurada
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Opcional: Interceptores para manejar errores o añadir tokens de autenticación
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("Error en la petición API:", error.response || error.message);
    // Aquí podrías añadir lógica para refrescar tokens, redirigir al login, etc.
    return Promise.reject(error);
  }
);

export default api;
