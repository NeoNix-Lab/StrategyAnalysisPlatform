import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, List, Activity, Database, Settings, LineChart, Target, BookOpen, Zap, BarChart2, ChevronLeft, ChevronRight, LogOut, Brain, Plug } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import StrategySelector from './StrategySelector'

const Layout = () => {
    const { user, logout } = useAuth()
    const location = useLocation()
    const [isCollapsed, setIsCollapsed] = useState(false)
    const [userWorkspace, setUserWorkspace] = useState('ANALYST') // 'ANALYST' | 'QUANT'

    const isActive = (path) => location.pathname === path

    const toggleSidebar = () => setIsCollapsed(!isCollapsed)

    // Theme Config based on Workspace
    const isAnalyst = userWorkspace === 'ANALYST'
    const activeColorClass = isAnalyst ? 'text-accent' : 'text-purple-400'
    const activeBgClass = isAnalyst ? 'bg-accent/10' : 'bg-purple-500/10'
    const railActiveGradient = isAnalyst
        ? 'bg-gradient-to-br from-blue-600/20 to-blue-700/20 border-blue-600/50 text-blue-400'
        : 'bg-gradient-to-br from-purple-600/20 to-purple-700/20 border-purple-600/50 text-purple-300'

    return (
        <div className="flex h-screen bg-bg text-text-primary overflow-hidden font-sans">
            {/* --- SIDEBAR CONTAINER --- */}
            <aside
                className={`${isCollapsed ? 'w-[72px]' : 'w-[300px]'} 
                bg-bg-secondary/70 backdrop-blur-xl border-r border-slate-700/50 
                flex flex-row transition-[width] duration-300 ease-out z-50 shrink-0`}
            >
                {/* --- LEFT RAIL (Workspace Activity Bar) --- */}
                <div className="w-[72px] bg-bg/60 border-r border-slate-700/30 flex flex-col items-center py-6 pb-4 gap-6 z-20 shrink-0">
                    <div className="flex flex-col gap-4 w-full items-center flex-1">
                        <button
                            onClick={() => setUserWorkspace('ANALYST')}
                            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 border border-transparent
                            ${userWorkspace === 'ANALYST'
                                    ? `${railActiveGradient} shadow-lg shadow-blue-900/20`
                                    : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}
                            title="Analyst Workspace"
                        >
                            <Activity size={24} strokeWidth={1.5} />
                        </button>
                        <button
                            onClick={() => setUserWorkspace('QUANT')}
                            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 border border-transparent
                            ${userWorkspace === 'QUANT'
                                    ? `${railActiveGradient} shadow-lg shadow-purple-900/20`
                                    : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}`}
                            title="Quant Lab Workspace"
                        >
                            <Brain size={24} strokeWidth={1.5} />
                        </button>
                    </div>

                    <button
                        className="w-8 h-8 rounded-full border border-white/10 bg-slate-800/80 text-text-secondary 
                        flex items-center justify-center hover:bg-white/10 hover:text-white hover:scale-110 transition-all mt-auto"
                        onClick={toggleSidebar}
                        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    >
                        {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                    </button>
                </div>

                {/* --- RIGHT PANEL (Navigation & Branding) --- */}
                <div
                    className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 
                    ${isCollapsed ? 'opacity-0 w-0 pointer-events-none' : 'opacity-100 min-w-0'}`}
                >
                    <div className="h-[72px] px-6 flex items-center justify-between border-b border-slate-700/50 shrink-0">
                        <h2 className="m-0 text-xl font-bold whitespace-nowrap bg-clip-text text-transparent bg-gradient-to-r from-accent to-indigo-400">
                            Quant Lab <span className="text-xs text-accent ml-1">V2</span>
                        </h2>
                    </div>

                    <nav className="p-4 flex flex-col gap-1 overflow-y-auto custom-scrollbar">
                        {userWorkspace === 'ANALYST' ? (
                            <>
                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-4 mb-2 pl-4 tracking-wider">Monitoring</div>
                                <NavLink to="/dashboard" icon={<LayoutDashboard size={20} />} label="Dashboard" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/trades" icon={<LineChart size={20} />} label="Trades" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/executions" icon={<List size={20} />} label="Executions" activeClass={`${activeBgClass} ${activeColorClass}`} />

                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-5 mb-2 pl-4 tracking-wider">Analytics</div>
                                <NavLink to="/analysis/setups" icon={<Target size={20} />} label="Setups" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/analysis/reports" icon={<BookOpen size={20} />} label="Reports" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/analysis/efficiency" icon={<Activity size={20} />} label="Efficiency" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/analysis/regime" icon={<BarChart2 size={20} />} label="Regime" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/analysis/stress-test" icon={<Zap size={20} />} label="Stress Test" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/analysis/compare" icon={<List size={20} />} label="Comparison" activeClass={`${activeBgClass} ${activeColorClass}`} />

                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-5 mb-2 pl-4 tracking-wider">System</div>
                                <NavLink to="/connections" icon={<Plug size={20} />} label="Connections" activeClass={`${activeBgClass} ${activeColorClass}`} />
                            </>
                        ) : (
                            <>
                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-4 mb-2 pl-4 tracking-wider">Laboratory</div>
                                <NavLink to="/ml/studio" icon={<LayoutDashboard size={20} />} label="Studio Home" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/ml/studio/compose" icon={<Zap size={20} />} label="Quick Train" activeClass={`${activeBgClass} ${activeColorClass}`} />

                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-5 mb-2 pl-4 tracking-wider">Assets</div>
                                <NavLink to="/datasets" icon={<Database size={20} />} label="Datasets" activeClass={`${activeBgClass} ${activeColorClass}`} />

                                <div className="text-[10px] uppercase font-bold text-slate-500 mt-5 mb-2 pl-4 tracking-wider">System</div>
                                <NavLink to="/connections" icon={<Plug size={20} />} label="Connections" activeClass={`${activeBgClass} ${activeColorClass}`} />
                                <NavLink to="/data" icon={<Database size={20} />} label="Data Management" activeClass={`${activeBgClass} ${activeColorClass}`} />
                            </>
                        )}

                        <div className="h-px bg-slate-800 my-2 mx-2"></div>
                        <NavLink to="/settings" icon={<Settings size={20} />} label="Settings" activeClass={`${activeBgClass} ${activeColorClass}`} />
                    </nav>

                    <div className="p-4 border-t border-slate-700/50 mt-auto">
                        <div className="flex items-center justify-between gap-2 text-text-secondary group">
                            <div className="flex flex-col overflow-hidden">
                                <span className="text-sm font-medium text-text-primary truncate max-w-[140px]" title={user?.email}>
                                    {user?.email}
                                </span>
                            </div>
                            <button
                                onClick={logout}
                                className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-500 transition-colors"
                                title="Logout"
                            >
                                <LogOut size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* --- MAIN CONTENT --- */}
            <main className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-[72px] flex justify-between items-center px-8 bg-bg-secondary/60 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-40">
                    <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                        <span>Strategy Analysis Platform</span>
                        <ChevronRight size={16} className="text-slate-600" />
                        <span className="text-accent font-semibold">
                            {location.pathname === '/'
                                ? 'Dashboard'
                                : location.pathname.split('/')[1]?.charAt(0).toUpperCase() + location.pathname.split('/')[1]?.slice(1) || 'Dashboard'
                            }
                        </span>
                    </div>
                    <div>
                        <StrategySelector />
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-8 relative">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}

// Helper Component for Nav Links
const NavLink = ({ to, icon, label, activeClass }) => {
    const location = useLocation()
    const isActive = location.pathname === to

    return (
        <Link
            to={to}
            className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all duration-200 hover:translate-x-1
            ${isActive
                    ? `${activeClass} font-medium`
                    : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'
                }`}
        >
            {icon}
            <span>{label}</span>
        </Link>
    )
}

export default Layout

