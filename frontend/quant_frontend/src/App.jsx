import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import Layout from './components/layout/Layout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import PrivateRoutes from './components/PrivateRoutes'
import Dashboard from './pages/Dashboard'
import Executions from './pages/Executions' // New Page
import Trades from './pages/Trades'
import TradeDetails from './pages/TradeDetails'
import Setups from './pages/Setups'
import Reports from './pages/Reports'
import TradeReplayPage from './pages/TradeReplayPage'
import Efficiency from './pages/Efficiency'
import Regime from './pages/Regime'
import StressTest from './pages/StressTest'
import DataManagement from './pages/DataManagement'
import Settings from './pages/Settings'
import Comparison from './pages/Comparison'

import MlDashboard from './pages/ml/MlDashboard'
import MlCompose from './pages/ml/MlCompose'
import MlSessionDetail from './pages/ml/MlSessionDetail' // Active
import MlTrainingRun from './pages/ml/MlTrainingRun' // Active
import Datasets from './pages/Datasets' // New
import MlStudioLayout from './pages/ml/MlStudioLayout'
import MlRewardFunctions from './pages/ml/MlRewardFunctions'
import MlModelArchitectures from './pages/ml/MlModelArchitectures'
import MlTrainingProcesses from './pages/ml/MlTrainingProcesses'
import MlModelRegistry from './pages/ml/MlModelRegistry'
import './App.css'

import LogDashboard from './components/LogDashboard'

function App() {
    return (
        <>
            <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Private Routes */}
                {/* Main Application Routes (Auth removed temporarily) */}
                <Route path="/" element={<Layout />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />

                    {/* --- ANALYST WORKSPACE --- */}
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="executions" element={<Executions />} />
                    <Route path="trades" element={<Trades />} />
                    <Route path="trades/:tradeId" element={<TradeDetails />} />
                    <Route path="trades/:tradeId/replay" element={<TradeReplayPage />} />

                    <Route path="analysis/setups" element={<Setups />} />
                    <Route path="analysis/reports" element={<Reports />} />
                    <Route path="analysis/efficiency" element={<Efficiency />} />
                    <Route path="analysis/regime" element={<Regime />} />
                    <Route path="analysis/stress-test" element={<StressTest />} />
                    <Route path="analysis/compare" element={<Comparison />} />


                    {/* --- QUANT LAB WORKSPACE --- */}
                    <Route path="ml" element={<Navigate to="/ml/studio" replace />} />

                    {/* Wrapped Studio Routes with Layout */}
                    <Route path="ml/studio" element={<MlStudioLayout />}>
                        <Route index element={<MlDashboard />} />
                        <Route path="compose" element={<MlCompose />} />
                        <Route path="registry" element={<MlModelRegistry />} />
                        <Route path="rewards" element={<MlRewardFunctions />} />
                        <Route path="models" element={<MlModelArchitectures />} />
                        <Route path="processes" element={<MlTrainingProcesses />} />
                        <Route path="session/:sessionId" element={<MlSessionDetail />} />
                        <Route path="session/:sessionId/run/:iterationId" element={<MlTrainingRun />} />
                    </Route>

                    <Route path="datasets" element={<Datasets />} />
                    <Route path="data" element={<DataManagement />} />
                    <Route path="settings" element={<Settings />} />
                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <LogDashboard />
        </>
    )
}

export default App
