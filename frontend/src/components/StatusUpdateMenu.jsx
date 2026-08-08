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
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteText, setNoteText] = useState('')
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

  function handleStatusClick(status) {
    if (status === 'failed') {
      setNoteText('')
      setShowNoteModal(true)
      setOpen(false)
    } else {
      mutation.mutate({ reference: shipment.reference, status })
    }
  }

  function confirmFailure() {
    mutation.mutate({
      reference: shipment.reference,
      status: 'failed',
      note: noteText.trim() || undefined,
    })
    setShowNoteModal(false)
  }

  return (
    <>
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
                  onClick={() => handleStatusClick(status)}
                >
                  <span className="dropdown-icon">{style.icon}</span>
                  {style.label}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {showNoteModal && (
        <div className="modal-overlay" onClick={() => setShowNoteModal(false)}>
          <div
            className="note-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="note-modal-header">
              <h3>❌ Mark as Failed</h3>
              <button className="modal-close" onClick={() => setShowNoteModal(false)}>✕</button>
            </div>
            <div className="note-modal-body">
              <label className="note-modal-label">
                Reason for failure <span className="note-optional">(optional)</span>
              </label>
              <textarea
                className="note-modal-input"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="e.g., Customer not available for pickup"
                autoFocus
                rows={3}
              />
            </div>
            <div className="note-modal-actions">
              <button
                className="note-modal-cancel"
                onClick={() => setShowNoteModal(false)}
              >
                Cancel
              </button>
              <button
                className="note-modal-confirm"
                onClick={confirmFailure}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? 'Updating...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
