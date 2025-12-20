import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check if user is logged in on mount
    useEffect(() => {
        checkUserLoggedIn();
    }, []);

    const checkUserLoggedIn = async () => {
        try {
            const response = await api.get('/auth/me');
            setUser(response.data);
            return true;
        } catch (error) {
            console.error("Check user logged in failed:", error);
            setUser(null);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email, password) => {
        // Form data for OAuth2PasswordRequestForm
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        // Login returns success but the cookie is HttpOnly
        // We receive access_token in body but rely on cookie for subsequent requests if configured that way.
        // Wait, standard OAuth2Password flows return access_token. 
        // My backend returns { access_token, token_type }.
        // If I want to use Bearer token, I need to store it.
        // Let's assume for this "Phase 1" we will store it in memory or localStorage 
        // because setting up HttpOnly cookie on backend requires more config (middleware response).

        // CORRECTION: Looking at backend code, it returns JSON token. 
        // It does NOT set a cookie automatically in `create_access_token` endpoint. 
        // So I must store the token.

        const response = await api.post('/auth/login', formData);
        const { access_token } = response.data;

        // Set default header for future requests
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        localStorage.setItem('token', access_token);

        // Fetch user details
        return await checkUserLoggedIn();
    };

    const register = async (email, password) => {
        const response = await api.post('/auth/register', { email, password });
        const { access_token } = response.data;

        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        localStorage.setItem('token', access_token);

        await checkUserLoggedIn();
        return true;
    };

    const logout = async () => {
        setUser(null);
        delete api.defaults.headers.common['Authorization'];
        localStorage.removeItem('token');
        // Optional: call backend logout if needed
    };

    // Initialize token from storage if exists
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
    }, []);

    return (
        <AuthContext.Provider value={{ user, login, register, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
