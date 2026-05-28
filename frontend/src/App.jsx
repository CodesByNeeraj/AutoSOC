import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Analyse from './pages/Analyse'
import Incidents from './pages/Incidents'
import Incident from './pages/Incident'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyse" element={<Analyse />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/incidents/:id" element={<Incident />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}