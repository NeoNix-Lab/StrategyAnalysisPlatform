import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App'
import { StrategyProvider } from './context/StrategyContext'

// Mock axios to prevent network errors during render
vi.mock('axios', () => ({
    default: {
        get: vi.fn(() => Promise.resolve({ data: [] }))
    }
}))

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

describe('App', () => {
    it('renders without crashing', () => {
        render(
            <StrategyProvider>
                <App />
            </StrategyProvider>
        )
        // Since App loads Dashboard by default, check for a common element if known, 
        // or just pass if render throws no error.
        // Ideally we mock the child components if they fetch data.
        // For now, just a basic render check.
        expect(document.body).toBeInTheDocument()

    })
})
