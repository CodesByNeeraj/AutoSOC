import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getIncidents, updateIncidentStatus } from '../services/api'

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

export default function Incidents() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  async function handleResolve(e, id) {
    e.stopPropagation()
    try {
      await updateIncidentStatus(id, 'resolved')
      setIncidents(prev => prev.map(i => i.id === id ? { ...i, status: 'resolved' } : i))
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    async function load() {
      try {
        const data = await getIncidents()
        setIncidents(data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = filter === 'all'
    ? incidents
    : incidents.filter(i => i.severity?.toLowerCase() === filter)

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Incidents</div>
          <div className="page-subtitle">{incidents.length} total incidents</div>
        </div>
        <button
          className="btn btn--primary"
          onClick={() => navigate('/analyse')}
        >
          new analysis →
        </button>
      </div>

      <div className="page-body">
        <div className="card">
          <div className="card-header">
            <span className="card-title">all incidents</span>
            {/*priority filters*/}
            <div style={{ display: 'flex', gap: '6px' }}>
              {['all', 'p0', 'p1', 'p2', 'p3', 'p4'].map(f => (
                <button
                  key={f}
                  className={`btn ${filter === f ? 'btn--primary' : 'btn--ghost'}`}
                  style={{ fontSize: '11px', padding: '4px 10px' }}
                  onClick={() => setFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="loading-bar">
              <div className="loading-bar-fill" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="empty-state">
              no incidents found
            </div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>priority</th>
                  <th>title</th>
                  <th>status</th>
                  <th>source</th>
                  <th>created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(inc => (
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
                      manual
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
      </div>
    </>
  )
}