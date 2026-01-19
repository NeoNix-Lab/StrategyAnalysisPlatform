import React, { useState } from 'react';
import { Lock, Shield, KeyRound, AlertCircle } from 'lucide-react';

const SecuritySection = () => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                    <Shield size={24} />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Security Settings</h3>
                    <p className="text-sm text-slate-400">Manage your password and account security.</p>
                </div>
            </div>

            <div className="max-w-xl">
                <form className="space-y-5 p-6 rounded-xl bg-slate-900/40 border border-slate-700/50 backdrop-blur-sm">
                    <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-2">Change Password</h4>

                    <div className="space-y-2">
                        <label className="text-sm text-slate-400">Current Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                            <input
                                type="password"
                                className="w-full bg-slate-950/50 border border-slate-700/70 rounded-lg pl-10 pr-4 py-2 text-slate-100 placeholder-slate-600 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 focus:outline-none transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm text-slate-400">New Password</label>
                            <div className="relative">
                                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                                <input
                                    type="password"
                                    className="w-full bg-slate-950/50 border border-slate-700/70 rounded-lg pl-10 pr-4 py-2 text-slate-100 placeholder-slate-600 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 focus:outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-slate-400">Confirm New</label>
                            <div className="relative">
                                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                                <input
                                    type="password"
                                    className="w-full bg-slate-950/50 border border-slate-700/70 rounded-lg pl-10 pr-4 py-2 text-slate-100 placeholder-slate-600 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 focus:outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="pt-2 flex justify-end">
                        <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg shadow-lg shadow-emerald-500/20 transition-all hover:translate-y-[-1px]">
                            Update Password
                        </button>
                    </div>
                </form>

                <div className="mt-8 p-4 rounded-lg bg-amber-500/5 border border-amber-500/20 flex gap-3 items-start">
                    <AlertCircle className="text-amber-500 shrink-0 mt-0.5" size={18} />
                    <div>
                        <h5 className="text-sm font-medium text-amber-400">Two-Factor Authentication (2FA)</h5>
                        <p className="text-xs text-amber-500/70 mt-1 mb-3">
                            Add an extra layer of security to your account by enabling 2FA.
                        </p>
                        <button className="text-xs font-semibold px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded border border-amber-500/30 transition-colors">
                            Enable 2FA
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SecuritySection;
