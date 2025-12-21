import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, List, Activity, Database, Settings, LineChart, Target, BookOpen, Zap, BarChart2, ChevronLeft, ChevronRight, LogOut, Brain } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import StrategySelector from './StrategySelector'
import './Layout.css'

const Layout = () => {
    const { user, logout } = useAuth()
    const location = useLocation()
    const [isCollapsed, setIsCollapsed] = useState(false)
    const [userWorkspace, setUserWorkspace] = useState('ANALYST') // 'ANALYST' | 'QUANT'

    const isActive = (path) => location.pathname === path

    const toggleSidebar = () => setIsCollapsed(!isCollapsed)

    return (
        <div className={`app-layout ${isCollapsed ? 'collapsed' : ''}`}>
            <aside className="sidebar">
                {/* --- LEFT RAIL (Workspace Activity Bar) --- */}
                <div className="sidebar-rail">
                    <div className="rail-group">
                        <button
                            onClick={() => setUserWorkspace('ANALYST')}
                            className={`rail-btn ${userWorkspace === 'ANALYST' ? 'active analyst' : ''}`}
                            title="Analyst Workspace"
                        >
                            <Activity size={24} strokeWidth={1.5} />
                        </button>
                        <button
                            onClick={() => setUserWorkspace('QUANT')}
                            className={`rail-btn ${userWorkspace === 'QUANT' ? 'active quant' : ''}`}
                            title="Quant Lab Workspace"
                        >
                            <Brain size={24} strokeWidth={1.5} />
                        </button>
                    </div>

                    <button
                        className="rail-toggle-btn"
                        onClick={toggleSidebar}
                        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    >
                        {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                    </button>
                </div>

                {/* --- RIGHT PANEL (Navigation & Branding) --- */}
                <div className="sidebar-content">
                    <div className="sidebar-header">
                        {!isCollapsed && (
                            <h2 className="brand-title">
                                Quant Lab <span className="brand-version">V2</span>
                            </h2>
                        )}
                    </div>

                    <nav className="sidebar-nav">
                        {userWorkspace === 'ANALYST' ? (
                            <>
                                <div className="nav-divider">{!isCollapsed ? "Monitoring" : "..."}</div>
                                <Link to="/dashboard" className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`} title="Dashboard">
                                    <LayoutDashboard size={20} />
                                    {!isCollapsed && <span>Dashboard</span>}
                                </Link>
                                <Link to="/trades" className={`nav-item ${isActive('/trades') ? 'active' : ''}`} title="Trades">
                                    <LineChart size={20} />
                                    {!isCollapsed && <span>Trades</span>}
                                </Link>
                                <Link to="/executions" className={`nav-item ${isActive('/executions') ? 'active' : ''}`} title="Executions">
                                    <List size={20} />
                                    {!isCollapsed && <span>Executions</span>}
                                </Link>

                                <div className="nav-divider">{!isCollapsed ? "Analytics" : "..."}</div>
                                <Link to="/analysis/setups" className={`nav-item ${isActive('/analysis/setups') ? 'active' : ''}`} title="Setups">
                                    <Target size={20} />
                                    {!isCollapsed && <span>Setups</span>}
                                </Link>
                                <Link to="/analysis/reports" className={`nav-item ${isActive('/analysis/reports') ? 'active' : ''}`} title="Reports">
                                    <BookOpen size={20} />
                                    {!isCollapsed && <span>Reports</span>}
                                </Link>
                                <Link to="/analysis/efficiency" className={`nav-item ${isActive('/analysis/efficiency') ? 'active' : ''}`} title="Efficiency">
                                    <Activity size={20} />
                                    {!isCollapsed && <span>Efficiency</span>}
                                </Link>
                                <Link to="/analysis/regime" className={`nav-item ${isActive('/analysis/regime') ? 'active' : ''}`} title="Regime">
                                    <BarChart2 size={20} />
                                    {!isCollapsed && <span>Regime</span>}
                                </Link>
                                <Link to="/analysis/stress-test" className={`nav-item ${isActive('/analysis/stress-test') ? 'active' : ''}`} title="Stress Test">
                                    <Zap size={20} />
                                    {!isCollapsed && <span>Stress Test</span>}
                                </Link>
                            </>
                        ) : (
                            <>
                                <div className="nav-divider">{!isCollapsed ? "Laboratory" : "..."}</div>
                                <Link to="/ml/studio" className={`nav-item ${isActive('/ml/studio') ? 'active' : ''}`} title="Studio Home">
                                    <LayoutDashboard size={20} className="text-purple-400" />
                                    {!isCollapsed && <span>Studio Home</span>}
                                </Link>
                                <Link to="/ml/studio/compose" className={`nav-item ${isActive('/ml/studio/compose') ? 'active' : ''}`} title="Quick Train">
                                    <Zap size={20} className="text-yellow-400" />
                                    {!isCollapsed && <span>Quick Train</span>}
                                </Link>

                                <div className="nav-divider">{!isCollapsed ? "Assets" : "..."}</div>
                                <Link to="/datasets" className={`nav-item ${isActive('/datasets') ? 'active' : ''}`} title="Datasets">
                                    <Database size={20} />
                                    {!isCollapsed && <span>Datasets</span>}
                                </Link>
                                {/* Future: Functions, Models pages */}

                                <div className="nav-divider">{!isCollapsed ? "System" : "..."}</div>
                                <Link to="/data" className={`nav-item ${isActive('/data') ? 'active' : ''}`} title="Data Management">
                                    <Database size={20} />
                                    {!isCollapsed && <span>Data Management</span>}
                                </Link>
                            </>
                        )}

                        <div className="nav-divider">{!isCollapsed ? "Global" : "..."}</div>
                        <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`} title="Settings">
                            <Settings size={20} />
                            {!isCollapsed && <span>Settings</span>}
                        </Link>
                    </nav>

                    <div className="sidebar-footer">
                        <div className="nav-divider">{!isCollapsed ? "User" : "..."}</div>
                        <div className="user-profile" title={user?.email}>
                            <div className="user-info">
                                {!isCollapsed && <span className="user-email">{user?.email}</span>}
                            </div>
                            <button onClick={logout} className="logout-btn" title="Logout">
                                <LogOut size={20} />
                                {!isCollapsed && <span>Logout</span>}
                            </button>
                        </div>
                    </div>
                </div> {/* End sidebar-content */}
            </aside>
            <main className="main-content-wrapper">
                <header className="topbar">
                    <div className="breadcrumbs">
                        <span>Strategy Analysis Platform</span>
                        <ChevronRight size={16} className="breadcrumb-separator" />
                        <span style={{ color: 'var(--accent)' }}>
                            {location.pathname === '/'
                                ? 'Dashboard'
                                : location.pathname.split('/')[1].charAt(0).toUpperCase() + location.pathname.split('/')[1].slice(1)
                            }
                        </span>
                    </div>
                    <div className="strategy-selector-wrapper">
                        <StrategySelector />
                    </div>
                </header>
                <div className="page-content">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}

export default Layout
