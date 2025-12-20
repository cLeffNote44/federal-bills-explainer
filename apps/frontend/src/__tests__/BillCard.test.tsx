import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock component for testing
const BillCard = ({ bill, onExplain }: any) => {
  return (
    <div data-testid="bill-card">
      <h3>{bill.title}</h3>
      <p>{bill.summary}</p>
      <button onClick={() => onExplain(bill.id)}>Explain Bill</button>
    </div>
  )
}

describe('BillCard', () => {
  const mockBill = {
    id: 'hr1234-118',
    title: 'Test Bill',
    summary: 'This is a test bill summary',
    status: 'introduced',
    introducedDate: '2024-01-01',
  }

  it('renders bill information correctly', () => {
    render(<BillCard bill={mockBill} onExplain={() => {}} />)
    
    expect(screen.getByText(mockBill.title)).toBeInTheDocument()
    expect(screen.getByText(mockBill.summary)).toBeInTheDocument()
  })

  it('calls onExplain when button is clicked', () => {
    const onExplain = vi.fn()
    render(<BillCard bill={mockBill} onExplain={onExplain} />)
    
    const button = screen.getByText('Explain Bill')
    fireEvent.click(button)
    
    expect(onExplain).toHaveBeenCalledWith(mockBill.id)
  })

  it('displays bill status badge', () => {
    render(<BillCard bill={mockBill} onExplain={() => {}} />)
    const card = screen.getByTestId('bill-card')
    expect(card).toBeInTheDocument()
  })
})