import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchShipments, fetchShipmentDetail, STATUS_ORDER, STATUS_LABELS } from '../api/shipments'
import StatusBadge from './StatusBadge'
import StatusUpdateMenu from './StatusUpdateMenu'
import ShipmentDetailModal from './ShipmentDetailModal'

export default function ShipmentList() {
  const [filter, setFilter] = useState('all')
  const [selectedRef, setSelectedRef] = useState(null)
  const [toast, setToast] = useState(null)

  const { data: shipments, isLoading, error } = useQuery({
    queryKey: ['shipments', filter],
    queryFn: () => fetchShipments(filter),
  })

  const { data: selectedShipment } = useQuery({
    queryKey: ['shipment', selectedRef],
    queryFn: () => fetchShipmentDetail(selectedRef),
    enabled: !!selectedRef,
  })

  function showToast(message, type) {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  function countByStatus(status) {
    if (!shipments) return 0
    return shipments.filter((s) => s.status === status).length
  }

  return (
    <div className="shipment-list">
      {/* Toast */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.type === 'error' ? '⚠️ ' : '✓ '}
          {toast.message}
        </div>
      )}

      {/* Filter tabs */}
      <div className="filter-tabs">
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All
          <span className="filter-count">
            {shipments?.length || 0}
          </span>
        </button>
        {STATUS_ORDER.map((status) => {
          const count = filter === 'all' ? countByStatus(status) : 0
          return (
            <button
              key={status}
              className={`filter-tab ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {STATUS_LABELS[status]}
              {filter === 'all' && count > 0 && (
                <span className="filter-count">{count}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Table */}
      <div className="table-container">
        {isLoading ? (
          <div className="table-placeholder">Loading shipments...</div>
        ) : error ? (
          <div className="table-placeholder error">
            Failed to load shipments. Is the API running on :8000?
          </div>
        ) : shipments?.length === 0 ? (
          <div className="table-placeholder">No shipments found for this filter.</div>
        ) : (
          <table className="shipments-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {shipments?.map((shipment) => (
                <tr
                  key={shipment.id}
                  className="shipment-row"
                  onClick={() => setSelectedRef(shipment.reference)}
                >
                  <td className="cell-ref">{shipment.reference}</td>
                  <td>{shipment.customer_name}</td>
                  <td><StatusBadge status={shipment.status} /></td>
                  <td className="cell-date">{formatDate(shipment.created_at)}</td>
                  <td className="cell-date">{formatDate(shipment.updated_at)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <StatusUpdateMenu
                      shipment={shipment}
                      onError={(msg) => showToast(msg, 'error')}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail modal */}
      {selectedShipment && (
        <ShipmentDetailModal
          shipment={selectedShipment}
          onClose={() => setSelectedRef(null)}
        />
      )}
    </div>
  )
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
