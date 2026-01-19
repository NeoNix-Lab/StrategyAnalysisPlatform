import axios from 'axios';

// Create a configured axios instance
// We use a relative URL so it works with the vite proxy or nginx later
// For development, ensure vite.config.js proxies /api to localhost:8000
const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

const getStoredToken = () => {
    try {
        return localStorage.getItem('token');
    } catch {
        return null;
    }
};

const clearStoredToken = () => {
    try {
        localStorage.removeItem('token');
    } catch {
        // Ignore storage errors
    }
    delete api.defaults.headers.common['Authorization'];
};

const applyAuthHeader = (headers, token) => {
    if (!token || !headers) return;
    if (typeof headers.set === 'function') {
        headers.set('Authorization', `Bearer ${token}`);
    } else if (!headers.Authorization) {
        headers.Authorization = `Bearer ${token}`;
    }
};

const existingToken = getStoredToken();
if (existingToken) {
    api.defaults.headers.common['Authorization'] = `Bearer ${existingToken}`;
}

// Request interceptor to add Distributed Tracing ID
api.interceptors.request.use(
    (config) => {
        config.headers = config.headers || {};
        // Generate a new Trace ID for every request if not present
        if (!config.headers['X-Trace-Id']) {
            config.headers['X-Trace-Id'] = crypto.randomUUID();
        }

        // Inject Authorization Header for JWT auth
        const token = getStoredToken();
        applyAuthHeader(config.headers, token);

        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle 401s (Unauthorized)
api.interceptors.response.use(
    (response) => {
        // We could also log the returned trace_id here for debugging
        // const traceId = response.headers['x-trace-id'];
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            const url = error.config?.url || '';
            const isAuthRoute = url.includes('/auth/login') || url.includes('/auth/register');
            if (!isAuthRoute) {
                clearStoredToken();
                if (typeof window !== 'undefined') {
                    window.dispatchEvent(new Event('auth:unauthorized'));
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;
