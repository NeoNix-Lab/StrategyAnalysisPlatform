import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';
import { SidebarProvider } from './context/SidebarContext';
import { AuthProvider } from './context/AuthContext';
import { StrategyProvider } from './context/StrategyContext';


ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <AuthProvider>
                <StrategyProvider>
                    <SidebarProvider>
                        <App />
                    </SidebarProvider>
                </StrategyProvider>
            </AuthProvider>
        </BrowserRouter>
    </React.StrictMode>
);
