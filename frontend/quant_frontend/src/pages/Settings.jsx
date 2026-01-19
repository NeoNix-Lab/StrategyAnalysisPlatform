import React, { useState } from 'react';
import { User, Shield, Settings as SettingsIcon, Key, ChevronRight } from 'lucide-react';
import ProfileSection from './settings/components/ProfileSection';
import SecuritySection from './settings/components/SecuritySection';
import PreferencesSection from './settings/components/PreferencesSection';
import ApiKeysSection from './settings/components/ApiKeysSection';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('profile');

    const tabs = [
        { id: 'profile', label: 'Profile Settings', icon: User, component: ProfileSection },
        { id: 'security', label: 'Security', icon: Shield, component: SecuritySection },
        { id: 'preferences', label: 'Preferences', icon: SettingsIcon, component: PreferencesSection },
        { id: 'api-keys', label: 'API Keys', icon: Key, component: ApiKeysSection },
    ];

    const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || ProfileSection;

    return (
        <div className="flex flex-col lg:flex-row gap-8 h-[calc(100vh-140px)]">
            {/* Sidebar Navigation */}
            <div className="w-full lg:w-64 flex-shrink-0 animate-slide-in">
                <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-700/50 p-4 sticky top-0">
                    <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 px-4 mb-6">
                        Account
                    </h2>
                    <nav className="space-y-1">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                                        ? 'bg-blue-600/10 text-blue-400 shadow-md shadow-blue-900/20 ring-1 ring-blue-500/20'
                                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <Icon size={18} className={isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-400'} />
                                        <span className="font-medium text-sm">{tab.label}</span>
                                    </div>
                                    {isActive && <ChevronRight size={16} className="text-blue-500 animate-pulse" />}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 animate-fade-in">
                <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-700/50 p-8 min-h-full shadow-xl shadow-black/20">
                    <ActiveComponent />
                </div>
            </div>
        </div>
    );
};

export default Settings;
