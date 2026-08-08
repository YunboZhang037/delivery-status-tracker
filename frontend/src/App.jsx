import ShipmentList from './components/ShipmentList'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="title-icon">🚀</span>
            Delivery Status Tracker
          </h1>
          <p className="app-subtitle">
            Track and manage shipment delivery statuses in real time
          </p>
        </div>
      </header>
      <main className="app-main">
        <ShipmentList />
      </main>
    </div>
  )
}
