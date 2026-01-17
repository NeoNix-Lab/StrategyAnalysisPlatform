import axios from 'axios';

// Create a configured axios instance
// We use a relative URL so it works with the vite proxy or nginx later
// For development, ensure vite.config.js proxies /api to localhost:8000
const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true // Crucial for sending/receiving HttpOnly cookies
});

// Request interceptor to add Distributed Tracing ID
api.interceptors.request.use(
    (config) => {
        // Generate a new Trace ID for every request if not present
        if (!config.headers['X-Trace-Id']) {
            config.headers['X-Trace-Id'] = crypto.randomUUID();
        }
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
            // If we get a 401, it means the session is invalid/expired.
            // We might want to trigger a global logout event here or let the AuthContext handle it.
            // For now, we reject the promise so the caller handles it.
        }
        return Promise.reject(error);
    }
);

export default api;
