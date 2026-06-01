import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getStats, getIncidents, updateIncidentStatus } from '../services/api'

const priorityColor = {
  p0: 'badge--p0',
  p1: 'badge--p1',
  p2: 'badge--p2',
  p3: 'badge--p3',
  p4: 'badge--p4',
}

const statusColor = {
  open: 'badge--investigating',
  complete: 'badge--investigating',
  resolved: 'badge--complete',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    async function load() {
      try {
        const [s, i] = await Promise.all([getStats(), getIncidents()])
        setStats(s)
        setIncidents(i.slice(0, 10))
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleResolve(e, id) {
    e.stopPropagation()
    try {
      await updateIncidentStatus(id, 'resolved')
      setIncidents(prev => prev.map(i => i.id === id ? { ...i, status: 'resolved' } : i))
      setStats(prev => prev ? { ...prev, open: prev.open - 1, resolved: (prev.resolved ?? 0) + 1 } : prev)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="page-subtitle">security operations overview</div>
        </div>
      </div>

      <div className="page-body">
        {loading ? (
          <div className="loading-bar">
            <div className="loading-bar-fill" />
          </div>
        ) : (
          <>
            {/*stats row*/}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">total incidents</div>
                <div className="stat-value stat-value--default">
                  {stats?.total ?? 0}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">open</div>
                <div className="stat-value stat-value--amber">
                  {stats?.open ?? 0}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">resolved</div>
                <div className="stat-value stat-value--green">
                  {stats?.resolved ?? 0}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">critical (p0)</div>
                <div className="stat-value stat-value--red">
                  {stats?.by_priority?.p0 ?? 0}
                </div>
              </div>
            </div>

            {/*recent incidents*/}
            <div className="card">
              <div className="card-header">
                <span className="card-title">recent incidents</span>
                <button
                  className="btn btn--ghost"
                  onClick={() => navigate('/incidents')}
                >
                  view all
                </button>
              </div>
              {incidents.length === 0 ? (
                <div className="empty-state">
                  no incidents found — submit an alert to get started
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>priority</th>
                      <th>title</th>
                      <th>status</th>
                      <th>created</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.map(inc => (
                      <tr
                        key={inc.id}
                        onClick={() => navigate(`/incidents/${inc.id}`)}
                      >
                        <td>
                          <span className={`badge ${priorityColor[inc.severity?.toLowerCase()] ?? 'badge--p4'}`}>
                            {inc.severity?.toLowerCase()}
                          </span>
                        </td>
                        <td>{inc.title}</td>
                        <td>
                          <span className={`badge ${statusColor[inc.status] ?? 'badge--investigating'}`}>
                            {inc.status}
                          </span>
                        </td>
                        <td className="mono" style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                          {new Date(inc.created_at).toLocaleString()}
                        </td>
                        <td onClick={e => e.stopPropagation()}>
                          {inc.status !== 'resolved' && inc.status !== 'investigating' ? (
                            <button
                              className="btn btn--resolve"
                              style={{ fontSize: '12px', padding: '5px 14px' }}
                              onClick={e => handleResolve(e, inc.id)}
                            >
                              ✓ resolve
                            </button>
                          ) : (
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}