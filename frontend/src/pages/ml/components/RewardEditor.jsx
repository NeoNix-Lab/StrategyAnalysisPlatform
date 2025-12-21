import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play } from 'lucide-react';

const RewardEditor = ({ code, setCode, onValidate, isValidating }) => {
    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#0f172a' }}>
            <div style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#e2e8f0' }}>Reward Function Logic</h3>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#64748b' }}>Define `calculate_reward(env, action)` in Python.</p>
                </div>
            </div>

            <div style={{ flex: 1, minHeight: '0' }}>
                <Editor
                    height="100%"
                    defaultLanguage="python"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    theme="vs-dark"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        padding: { top: 16, bottom: 16 }
                    }}
                />
            </div>
        </div>
    );
};

export default RewardEditor;
