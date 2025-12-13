import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, List, Activity, Database, Settings } from 'lucide-react'
import StrategySelector from './StrategySelector'
import './Layout.css'

const Layout = () => {
    const location = useLocation()

    const isActive = (path) => location.pathname === path

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>Quant Lab <span style={{ fontSize: '0.7em', color: 'var(--accent)' }}>V2</span></h2>
                </div>
                <nav className="sidebar-nav">
                    <Link to="/" className={`nav-item ${isActive('/') ? 'active' : ''}`}>
                        <LayoutDashboard size={20} />
                        <span>Dashboard</span>
                    </Link>

                    {/* Replaces Trades */}
                    <Link to="/executions" className={`nav-item ${isActive('/executions') ? 'active' : ''}`}>
                        <List size={20} />
                        <span>Executions</span>
                    </Link>

                    {/* Temporary Placeholder for Analytics */}
                    <div className="nav-divider">Analytics (Coming Soon)</div>
                    <div className="nav-item disabled">
                        <Activity size={20} />
                        <span>Efficiency</span>
                    </div>

                    <div className="nav-divider">System</div>
                    <Link to="/data" className={`nav-item ${isActive('/data') ? 'active' : ''}`}>
                        <Database size={20} />
                        <span>Data Management</span>
                    </Link>
                    <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`}>
                        <Settings size={20} />
                        <span>Settings</span>
                    </Link>
                </nav>
            </aside>
            <main className="main-content-wrapper">
                <header className="topbar">
                    <div className="breadcrumbs">
                        Strategy Analysis Platform / {location.pathname === '/' ? 'Dashboard' : location.pathname.substring(1).charAt(0).toUpperCase() + location.pathname.substring(2)}
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
