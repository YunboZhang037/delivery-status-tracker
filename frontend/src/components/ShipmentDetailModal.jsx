import { STATUS_LABELS } from '../api/shipments'
import StatusBadge from './StatusBadge'

export default function ShipmentDetailModal({ shipment, onClose, loading }) {
  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-loading">
            <div className="modal-spinner" />
            <p>Loading shipment details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!shipment) return null

  const history = shipment.history || []

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">{shipment.reference}</h2>
            <p className="modal-subtitle">{shipment.customer_name}</p>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Current Status</span>
              <StatusBadge status={shipment.status} />
            </div>
            <div className="detail-item">
              <span className="detail-label">Reference</span>
              <span className="detail-value">{shipment.reference}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Customer</span>
              <span className="detail-value">{shipment.customer_name}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Created</span>
              <span className="detail-value">{formatDateTime(shipment.created_at)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Last Updated</span>
              <span className="detail-value">{formatDateTime(shipment.updated_at)}</span>
            </div>
          </div>

          <div className="history-section">
            <h3 className="history-title">Status History</h3>
            {history.length === 0 ? (
              <p className="history-empty">No status changes recorded yet.</p>
            ) : (
              <div className="timeline">
                {history.map((entry, idx) => (
                  <div className="timeline-item" key={entry.id}>
                    <div className="timeline-marker">
                      <div className={`timeline-dot ${idx === history.length - 1 ? 'active' : ''}`} />
                      {idx < history.length - 1 && <div className="timeline-line" />}
                    </div>
                    <div className="timeline-content">
                      <div className="timeline-statuses">
                        {entry.previous_status && (
                          <>
                            <StatusBadge status={entry.previous_status} />
                            <span className="timeline-arrow">→</span>
                          </>
                        )}
                        <StatusBadge status={entry.new_status} />
                      </div>
                      <span className="timeline-time">
                        {formatDateTime(entry.changed_at)}
                      </span>
                      {entry.note && (
                        <span className="timeline-note">{entry.note}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
