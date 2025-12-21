import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play } from 'lucide-react';

const RewardEditor = ({ code, setCode, onMount }) => {
    const handleEditorDidMount = (editor, monaco) => {
        if (onMount) onMount(editor, monaco);
    };

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#0f172a' }}>
            <div style={{ flex: 1, minHeight: '0' }}>
                <Editor
                    height="100%"
                    defaultLanguage="python"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    onMount={handleEditorDidMount}
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
            <div style={{ padding: '0.5rem 1rem', borderTop: '1px solid #334155', fontSize: '0.75rem', color: '#64748b', background: '#1e293b' }}>
                Editor Mode: Python (Monaco)
            </div>
        </div>
    );
};

export default RewardEditor;
