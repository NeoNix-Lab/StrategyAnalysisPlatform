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

    const isActive = (path) => location.pathname === path

    const toggleSidebar = () => setIsCollapsed(!isCollapsed)

    return (
        <div className={`app-layout ${isCollapsed ? 'collapsed' : ''}`}>
            <aside className="sidebar">
                <div className="sidebar-header">
                    {!isCollapsed && (
                        <h2 className="brand-title">
                            Quant Lab <span className="brand-version">V2</span>
                        </h2>
                    )}
                    <button className="sidebar-toggle" onClick={toggleSidebar}>
                        {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                    </button>
                </div>
                <nav className="sidebar-nav">
                    <Link to="/" className={`nav-item ${isActive('/') ? 'active' : ''}`} title={isCollapsed ? "Dashboard" : ""}>
                        <LayoutDashboard size={20} />
                        {!isCollapsed && <span>Dashboard</span>}
                    </Link>

                    <Link to="/trades" className={`nav-item ${isActive('/trades') ? 'active' : ''}`} title={isCollapsed ? "Trades" : ""}>
                        <LineChart size={20} />
                        {!isCollapsed && <span>Trades</span>}
                    </Link>
                    <Link to="/executions" className={`nav-item ${isActive('/executions') ? 'active' : ''}`} title={isCollapsed ? "Executions" : ""}>
                        <List size={20} />
                        {!isCollapsed && <span>Executions</span>}
                    </Link>

                    <div className="nav-divider">{!isCollapsed ? "Analytics" : "..."}</div>

                    <Link to="/analysis/setups" className={`nav-item ${isActive('/analysis/setups') ? 'active' : ''}`} title={isCollapsed ? "Setups" : ""}>
                        <Target size={20} />
                        {!isCollapsed && <span>Setups</span>}
                    </Link>
                    <Link to="/analysis/reports" className={`nav-item ${isActive('/analysis/reports') ? 'active' : ''}`} title={isCollapsed ? "Reports" : ""}>
                        <BookOpen size={20} />
                        {!isCollapsed && <span>Reports</span>}
                    </Link>
                    <Link to="/analysis/efficiency" className={`nav-item ${isActive('/analysis/efficiency') ? 'active' : ''}`} title={isCollapsed ? "Efficiency" : ""}>
                        <Activity size={20} />
                        {!isCollapsed && <span>Efficiency</span>}
                    </Link>
                    <Link to="/analysis/regime" className={`nav-item ${isActive('/analysis/regime') ? 'active' : ''}`} title={isCollapsed ? "Regime" : ""}>
                        <BarChart2 size={20} />
                        {!isCollapsed && <span>Regime</span>}
                    </Link>
                    <Link to="/analysis/stress-test" className={`nav-item ${isActive('/analysis/stress-test') ? 'active' : ''}`} title={isCollapsed ? "Stress Test" : ""}>
                        <Zap size={20} />
                        {!isCollapsed && <span>Stress Test</span>}
                    </Link>
                    <Link to="/ml" className={`nav-item ${isActive('/ml') ? 'active' : ''}`} title={isCollapsed ? "Machine Learning" : ""}>
                        <Brain size={20} />
                        {!isCollapsed && <span>Machine Learning</span>}
                    </Link>
                    <Link to="/datasets" className={`nav-item ${isActive('/datasets') ? 'active' : ''}`} title={isCollapsed ? "Datasets" : ""}>
                        <Database size={20} />
                        {!isCollapsed && <span>Datasets</span>}
                    </Link>

                    <div className="nav-divider">{!isCollapsed ? "System" : "..."}</div>

                    <Link to="/data" className={`nav-item ${isActive('/data') ? 'active' : ''}`} title={isCollapsed ? "Data Management" : ""}>
                        <Database size={20} />
                        {!isCollapsed && <span>Data Management</span>}
                    </Link>
                    <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`} title={isCollapsed ? "Settings" : ""}>
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
