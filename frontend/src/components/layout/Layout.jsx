import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, BarChart2, List, Settings, PieChart, Activity, Database } from 'lucide-react'
import StrategySelector from './StrategySelector'
import './Layout.css'

const Layout = () => {
    const location = useLocation()

    const isActive = (path) => location.pathname === path

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>Quant Lab</h2>
                </div>
                <nav className="sidebar-nav">
                    <Link to="/" className={`nav-item ${isActive('/') ? 'active' : ''}`}>
                        <LayoutDashboard size={20} />
                        <span>Dashboard</span>
                    </Link>
                    <Link to="/efficiency" className={`nav-item ${isActive('/efficiency') ? 'active' : ''}`}>
                        <Activity size={20} />
                        <span>Efficiency</span>
                    </Link>
                    <Link to="/trades" className={`nav-item ${isActive('/trades') ? 'active' : ''}`}>
                        <List size={20} />
                        <span>Trades</span>
                    </Link>
                    <Link to="/regime" className={`nav-item ${isActive('/regime') ? 'active' : ''}`}>
                        <PieChart size={20} />
                        <span>Regime</span>
                    </Link>
                    <Link to="/data" className={`nav-item ${isActive('/data') ? 'active' : ''}`}>
                        <Database size={20} />
                        <span>Data</span>
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
                    <div className="strategy-selector">
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
