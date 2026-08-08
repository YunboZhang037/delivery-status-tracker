import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function fetchShipments(status) {
  const params = status && status !== 'all' ? { status } : {}
  const { data } = await api.get('/shipments', { params })
  return data
}

export async function fetchShipmentDetail(reference) {
  const { data } = await api.get(`/shipments/${reference}`)
  return data
}

export async function updateShipmentStatus(reference, newStatus) {
  const { data } = await api.patch(`/shipments/${reference}/status`, {
    status: newStatus,
  })
  return data
}

// State machine transition map — drives the UI action buttons
export const VALID_TRANSITIONS = {
  created: ['picked_up', 'failed'],
  picked_up: ['in_transit', 'failed'],
  in_transit: ['delivered', 'failed'],
  delivered: [],
  failed: [],
}

export const STATUS_LABELS = {
  created: 'Created',
  picked_up: 'Picked Up',
  in_transit: 'In Transit',
  delivered: 'Delivered',
  failed: 'Failed',
}

export const STATUS_ORDER = ['created', 'picked_up', 'in_transit', 'delivered', 'failed']
