import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './App.css'

import { StrategyProvider } from './context/StrategyContext.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <StrategyProvider>
            <App />
        </StrategyProvider>
    </React.StrictMode>,
)
