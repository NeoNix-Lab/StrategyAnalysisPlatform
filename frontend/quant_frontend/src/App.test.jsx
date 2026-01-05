import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App'
import { StrategyProvider } from './context/StrategyContext'

// Mock axios to prevent network errors during render
// Mock axios to prevent network errors during render
vi.mock('axios', () => {
    const mockInstance = {
        get: vi.fn(() => Promise.resolve({ data: [] })),
        post: vi.fn(() => Promise.resolve({ data: [] })),
        interceptors: {
            request: { use: vi.fn() },
            response: { use: vi.fn() }
        }
    };

    return {
        default: {
            ...mockInstance,
            create: vi.fn(() => mockInstance)
        }
    }
})

// Mock Recharts to avoid issues with ResponsiveContainer in tests
vi.mock('recharts', () => ({
    ResponsiveContainer: ({ children }) => <div>{children}</div>,
    LineChart: () => <div>LineChart</div>,
    Line: () => <div>Line</div>,
    XAxis: () => <div>XAxis</div>,
    YAxis: () => <div>YAxis</div>,
    CartesianGrid: () => <div>CartesianGrid</div>,
    Tooltip: () => <div>Tooltip</div>
}))

import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'

describe('App', () => {
    it('renders without crashing', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <StrategyProvider>
                        <App />
                    </StrategyProvider>
                </AuthProvider>
            </MemoryRouter>
        )
        // Since App loads Dashboard by default, check for a common element if known, 
        // or just pass if render throws no error.
        // Ideally we mock the child components if they fetch data.
        // For now, just a basic render check.
        expect(document.body).toBeInTheDocument()

    })
})
