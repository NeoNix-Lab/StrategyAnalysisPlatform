import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Executions from './pages/Executions' // New Page
import Trades from './pages/Trades'
import TradeDetails from './pages/TradeDetails'
import Setups from './pages/Setups'
import Reports from './pages/Reports'
import Efficiency from './pages/Efficiency'
import Regime from './pages/Regime'
import StressTest from './pages/StressTest'
import DataManagement from './pages/DataManagement'
import Settings from './pages/Settings'
import './App.css'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="executions" element={<Executions />} />
                    <Route path="trades" element={<Trades />} />
                    <Route path="trades/:tradeId" element={<TradeDetails />} />

                    {/* Analytics Routes */}
                    <Route path="analysis/setups" element={<Setups />} />
                    <Route path="analysis/reports" element={<Reports />} />
                    <Route path="analysis/efficiency" element={<Efficiency />} />
                    <Route path="analysis/regime" element={<Regime />} />
                    <Route path="analysis/stress-test" element={<StressTest />} />

                    <Route path="data" element={<DataManagement />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    )
}

export default App
