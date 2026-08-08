import { useState, useRef, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateShipmentStatus, VALID_TRANSITIONS, STATUS_LABELS } from '../api/shipments'

const ACTION_STYLES = {
  picked_up: { icon: '📦', label: 'Mark Picked Up' },
  in_transit: { icon: '🚚', label: 'Mark In Transit' },
  delivered: { icon: '✅', label: 'Mark Delivered' },
  failed: { icon: '❌', label: 'Mark Failed' },
}

export default function StatusUpdateMenu({ shipment, onError }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: ({ reference, status, note }) => updateShipmentStatus(reference, status, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shipments'] })
      queryClient.invalidateQueries({ queryKey: ['shipment', shipment.reference] })
      setOpen(false)
    },
    onError: (err) => {
      const detail = err.response?.data?.detail || 'Failed to update status'
      onError?.(detail)
      setOpen(false)
    },
  })

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const nextStatuses = VALID_TRANSITIONS[shipment.status] || []

  if (nextStatuses.length === 0) {
    return <span className="terminal-label">—</span>
  }

  return (
    <div className="status-update-menu" ref={ref}>
      <button
        className="update-btn"
        onClick={() => setOpen(!open)}
        disabled={mutation.isPending}
      >
        {mutation.isPending ? 'Updating...' : 'Update ▾'}
      </button>
      {open && (
        <div className="dropdown-menu">
          {nextStatuses.map((status) => {
            const style = ACTION_STYLES[status]
            return (
              <button
                key={status}
                className="dropdown-item"
                onClick={() => {
                  if (status === 'failed') {
                    const note = window.prompt('Optional: enter a reason for failure (can be left blank)')
                    if (note === null) return
                    mutation.mutate({ reference: shipment.reference, status, note: note || undefined })
                  } else {
                    mutation.mutate({ reference: shipment.reference, status })
                  }
                }}
              >
                <span className="dropdown-icon">{style.icon}</span>
                {style.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
