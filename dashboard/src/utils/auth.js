// JWT Auth helpers for SmartShift+ Worker Portal
const TOKEN_KEY = 'smartshift_token';
const WORKER_KEY = 'smartshift_worker';

export const saveAuth = (token, workerData) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(WORKER_KEY, JSON.stringify(workerData));
};

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const getWorker = () => {
  const w = localStorage.getItem(WORKER_KEY);
  return w ? JSON.parse(w) : null;
};

export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(WORKER_KEY);
};

export const isLoggedIn = () => !!getToken();

// Authenticated fetch helper — adds Bearer token automatically
export const authFetch = async (url, options = {}) => {
  const token = getToken();
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
};

export const BASE_URL = 'http://localhost:8000/api';
export const API = 'http://localhost:8000/api/auth';
