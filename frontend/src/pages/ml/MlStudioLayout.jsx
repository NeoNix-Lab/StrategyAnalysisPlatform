import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Layers, Brain, Zap, PenTool, LayoutDashboard } from 'lucide-react';
import '../Dashboard.css'; // Ensure uniformity

const MlStudioLayout = () => {
    const location = useLocation();

    const navItems = [
        { path: '/ml/studio', label: 'Dashboard', icon: LayoutDashboard, exact: true },
        { path: '/ml/studio/compose', label: 'Compose Session', icon: PenTool },
        { path: '/ml/studio/rewards', label: 'Reward Functions', icon: Brain },
        { path: '/ml/studio/models', label: 'Architectures', icon: Layers },
        { path: '/ml/studio/processes', label: 'Training Configs', icon: Zap },
    ];

    return (
        <div className="dashboard-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0' }}>
            {/* Sub-Navigation Header */}
            <div style={{
                borderBottom: '1px solid #334155',
                padding: '0 2rem',
                background: 'rgba(15, 23, 42, 0.6)',
                display: 'flex',
                gap: '2rem',
                alignItems: 'center',
                height: '60px'
            }}>
                {navItems.map((item) => {
                    const isActive = item.exact
                        ? location.pathname === item.path
                        : location.pathname.startsWith(item.path);

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.exact}
                            style={({ isActive }) => ({
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                padding: '1rem 0',
                                color: isActive ? '#d8b4fe' : '#94a3b8',
                                borderBottom: isActive ? '2px solid #a855f7' : '2px solid transparent',
                                textDecoration: 'none',
                                fontWeight: isActive ? 600 : 500,
                                fontSize: '0.9rem',
                                transition: 'all 0.2s'
                            })}
                        >
                            <item.icon size={18} />
                            {item.label}
                        </NavLink>
                    );
                })}
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
                <Outlet />
            </div>
        </div>
    );
};

export default MlStudioLayout;
