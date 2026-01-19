import React, { useState } from 'react';
import { Settings, Bell, Moon, Sun, Monitor, Globe } from 'lucide-react';

const PreferencesSection = () => {
    const [theme, setTheme] = useState('dark');
    const [notifications, setNotifications] = useState({
        email: true,
        push: false,
        trades: true,
        system: true
    });

    const toggleNotification = (key) => {
        setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
    };

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
                    <Settings size={24} />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Preferences</h3>
                    <p className="text-sm text-slate-400">Customize your platform experience.</p>
                </div>
            </div>

            <div className="max-w-2xl space-y-6">

                {/* Theme Selection */}
                <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-700/50 backdrop-blur-sm">
                    <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Monitor size={16} /> Interface Theme
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                        <button
                            onClick={() => setTheme('dark')}
                            className={`p-4 rounded-lg border flex flex-col items-center gap-3 transition-all ${theme === 'dark'
                                    ? 'bg-blue-600/10 border-blue-500 text-blue-400 ring-1 ring-blue-500/50'
                                    : 'bg-slate-950/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                                }`}
                        >
                            <Moon size={24} />
                            <span className="text-sm font-medium">Dark Mode</span>
                        </button>
                        <button
                            onClick={() => setTheme('light')}
                            className={`p-4 rounded-lg border flex flex-col items-center gap-3 transition-all ${theme === 'light'
                                    ? 'bg-blue-600/10 border-blue-500 text-blue-400 ring-1 ring-blue-500/50'
                                    : 'bg-slate-950/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                                }`}
                        >
                            <Sun size={24} />
                            <span className="text-sm font-medium">Light Mode</span>
                        </button>
                        <button
                            onClick={() => setTheme('system')}
                            className={`p-4 rounded-lg border flex flex-col items-center gap-3 transition-all ${theme === 'system'
                                    ? 'bg-blue-600/10 border-blue-500 text-blue-400 ring-1 ring-blue-500/50'
                                    : 'bg-slate-950/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                                }`}
                        >
                            <Monitor size={24} />
                            <span className="text-sm font-medium">System</span>
                        </button>
                    </div>
                </div>

                {/* Notifications */}
                <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-700/50 backdrop-blur-sm">
                    <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Bell size={16} /> Notifications
                    </h4>
                    <div className="space-y-4">
                        {['email', 'push', 'trades', 'system'].map((key) => (
                            <div key={key} className="flex items-center justify-between py-2">
                                <div>
                                    <p className="text-sm font-medium text-slate-200 capitalize">{key} Notifications</p>
                                    <p className="text-xs text-slate-500">Receive updates via {key}.</p>
                                </div>
                                <button
                                    onClick={() => toggleNotification(key)}
                                    className={`relative w-11 h-6 rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${notifications[key] ? 'bg-blue-600' : 'bg-slate-700'
                                        }`}
                                >
                                    <span
                                        className={`inline-block w-4 h-4 transform transition duration-200 ease-in-out bg-white rounded-full ${notifications[key] ? 'translate-x-6' : 'translate-x-1'
                                            } mt-1`}
                                    />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Regional */}
                <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-700/50 backdrop-blur-sm">
                    <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Globe size={16} /> Region & Timezone
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm text-slate-400">Language</label>
                            <select className="w-full bg-slate-950/50 border border-slate-700/70 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500">
                                <option>English (US)</option>
                                <option>Spanish</option>
                                <option>French</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-slate-400">Timezone</label>
                            <select className="w-full bg-slate-950/50 border border-slate-700/70 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500">
                                <option>UTC (GMT+00:00)</option>
                                <option>EST (GMT-05:00)</option>
                                <option>PST (GMT-08:00)</option>
                            </select>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default PreferencesSection;
