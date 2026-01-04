import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Layers, Brain, Zap, PenTool, LayoutDashboard, Box } from 'lucide-react';

const MlStudioLayout = () => {
    const location = useLocation();

    const navItems = [
        { path: '/ml/studio', label: 'Dashboard', icon: LayoutDashboard, exact: true },
        { path: '/ml/studio/compose', label: 'Compose Session', icon: PenTool },
        { path: '/ml/studio/registry', label: 'Model Registry', icon: Box },
        { path: '/ml/studio/rewards', label: 'Reward Functions', icon: Brain },
        { path: '/ml/studio/models', label: 'Architectures', icon: Layers },
        { path: '/ml/studio/processes', label: 'Training Configs', icon: Zap },
    ];

    return (
        <div className="flex flex-col h-full bg-bg-primary overflow-hidden">
            {/* Sub-Navigation Header */}
            <div className="border-b border-slate-700/50 bg-slate-900/60 backdrop-blur-md px-8 h-[60px] flex items-center gap-8 shadow-lg z-10">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.exact}
                        className={({ isActive }) => `
                            flex items-center gap-2 h-full text-sm font-medium transition-all duration-200 border-b-2
                            ${isActive
                                ? 'text-violet-400 border-violet-500'
                                : 'text-slate-400 border-transparent hover:text-slate-200 hover:border-slate-700'}
                        `}
                    >
                        <item.icon size={18} />
                        {item.label}
                    </NavLink>
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar relative">
                <div className="max-w-[1600px] mx-auto">
                    <Outlet />
                </div>
            </div>
        </div>
    );
};

export default MlStudioLayout;
