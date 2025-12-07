import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Efficiency from './pages/Efficiency'
import Trades from './pages/Trades'
import Regime from './pages/Regime'
import Parameters from './pages/Parameters'
import StressTest from './pages/StressTest'
import Setups from './pages/Setups'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import DataManagement from './pages/DataManagement'
import TradeDetails from './pages/TradeDetails'
import './App.css'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="efficiency" element={<Efficiency />} />
                    <Route path="trades" element={<Trades />} />
                    <Route path="trades/:tradeId" element={<TradeDetails />} />
                    <Route path="regime" element={<Regime />} />
                    <Route path="parameters" element={<Parameters />} />
                    <Route path="stress" element={<StressTest />} />
                    <Route path="setups" element={<Setups />} />
                    <Route path="reports" element={<Reports />} />
                    <Route path="data" element={<DataManagement />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    )
}

export default App
