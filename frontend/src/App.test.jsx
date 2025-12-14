import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
    it('renders without crashing', () => {
        render(<App />)
        // Since App loads Dashboard by default, check for a common element if known, 
        // or just pass if render throws no error.
        // Ideally we mock the child components if they fetch data.
        // For now, just a basic render check.
        expect(document.body).toBeInTheDocument()
    })
})
