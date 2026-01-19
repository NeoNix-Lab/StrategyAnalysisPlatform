import React, { useState } from 'react';
import { User, Mail, Camera, Save } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';

const ProfileSection = () => {
    const { user } = useAuth();
    const [name, setName] = useState(user?.name || '');
    const [email, setEmail] = useState(user?.email || '');
    const [isEditing, setIsEditing] = useState(false);

    const handleSave = (e) => {
        e.preventDefault();
        // Implement save logic here
        setIsEditing(false);
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-4">
                <div className="relative group">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 p-0.5 shadow-lg shadow-blue-500/20">
                        <div className="w-full h-full rounded-full bg-slate-900 flex items-center justify-center overflow-hidden">
                            <span className="text-2xl font-bold text-white">
                                {user?.email?.[0].toUpperCase() || 'U'}
                            </span>
                        </div>
                    </div>
                    <button className="absolute bottom-0 right-0 p-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors shadow-lg">
                        <Camera size={14} />
                    </button>
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Profile Information</h3>
                    <p className="text-sm text-slate-400">Update your photo and personal details.</p>
                </div>
            </div>

            <form onSubmit={handleSave} className="space-y-4 max-w-xl">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Display Name</label>
                    <div className="relative group">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            disabled={!isEditing}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                            placeholder="Your Name"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Email Address</label>
                    <div className="relative group">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={18} />
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            disabled={true} // Usually email is managed separately for security
                            className="w-full bg-slate-900/30 border border-slate-700/50 rounded-lg pl-10 pr-4 py-2.5 text-slate-400 cursor-not-allowed"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-600">
                            Managed by Auth
                        </span>
                    </div>
                </div>

                <div className="pt-4 flex items-center gap-3">
                    {isEditing ? (
                        <>
                            <button
                                type="submit"
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-600/20"
                            >
                                <Save size={18} />
                                Save Changes
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsEditing(false)}
                                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-colors border border-slate-700"
                            >
                                Cancel
                            </button>
                        </>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setIsEditing(true)}
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors border border-slate-700 shadow-sm"
                        >
                            Edit Profile
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
};

export default ProfileSection;
