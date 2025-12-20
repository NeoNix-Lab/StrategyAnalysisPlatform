import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
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
import MachineLearning from './pages/MachineLearning'
import MlDashboard from './pages/ml/MlDashboard'
import MlCompose from './pages/ml/MlCompose'
import MlSessionDetail from './pages/ml/MlSessionDetail' // Active
import MlTrainingRun from './pages/ml/MlTrainingRun' // Active
import Datasets from './pages/Datasets' // New
import './App.css'

function App() {
    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Private Routes */}
            {/* Main Application Routes (Auth removed temporarily) */}
            <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="executions" element={<Executions />} />
                <Route path="trades" element={<Trades />} />
                <Route path="trades/:tradeId" element={<TradeDetails />} />
                <Route path="trades/:tradeId/replay" element={<TradeReplayPage />} />

                {/* Analytics Routes */}
                <Route path="analysis/setups" element={<Setups />} />
                <Route path="analysis/reports" element={<Reports />} />
                <Route path="analysis/efficiency" element={<Efficiency />} />
                <Route path="analysis/stress-test" element={<StressTest />} />

                <Route path="ml/studio" element={<MlDashboard />} />
                <Route path="ml/studio/compose" element={<MlCompose />} />
                <Route path="ml/studio/session/:sessionId" element={<MlSessionDetail />} />
                <Route path="ml/studio/session/:sessionId/run/:iterationId" element={<MlTrainingRun />} />
                <Route path="datasets" element={<Datasets />} /> {/* New Route */}
                <Route path="data" element={<DataManagement />} />
                <Route path="settings" element={<Settings />} />
            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
