import { STATUS_LABELS } from '../api/shipments'

const STATUS_COLORS = {
  created: { bg: '#e9ecef', text: '#495057', dot: '#6c757d' },
  picked_up: { bg: '#fff3cd', text: '#664d03', dot: '#ffc107' },
  in_transit: { bg: '#d1ecf9', text: '#0c5460', dot: '#17a2b8' },
  delivered: { bg: '#d4edda', text: '#155724', dot: '#28a745' },
  failed: { bg: '#f8d7da', text: '#721c24', dot: '#dc3545' },
}

export default function StatusBadge({ status }) {
  const colors = STATUS_COLORS[status] || STATUS_COLORS.created
  const label = STATUS_LABELS[status] || status

  return (
    <span
      className="status-badge"
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
      }}
    >
      <span className="status-dot" style={{ backgroundColor: colors.dot }} />
      {label}
    </span>
  )
}
