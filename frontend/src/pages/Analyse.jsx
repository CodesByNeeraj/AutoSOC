import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyseAlert } from '../services/api'

const sampleLogs = [
  {
    label: 'brute force',
    log: 'Failed login attempt for user admin from IP 192.168.1.105 at 03:42:11. 47 attempts in 2 minutes. Account locked after threshold exceeded. Source IP flagged in threat intel database.'
  },
  {
    label: 'lateral movement',
    log: 'Unusual SMB traffic detected from workstation WS-042 to domain controller DC-01. User account svc_backup accessing multiple file shares outside business hours. 3 failed authentication attempts followed by successful login.'
  },
  {
    label: 'data exfiltration',
    log: 'Large outbound transfer detected: 4.2GB sent from 10.0.0.45 to external IP 185.220.101.47 over port 443. Process: svchost.exe. Transfer duration: 12 minutes. Destination IP associated with known C2 infrastructure.'
  }
]

const ACCEPTED_TYPES = ['.log', '.txt', '.json', '.csv']

export default function Analyse() {
  const [log, setLog] = useState('')
  const [source, setSource] = useState('manual')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [inputMode, setInputMode] = useState('text')
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef(null)
  const navigate = useNavigate()

  function readFile(file) {
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`unsupported file type — accepted: ${ACCEPTED_TYPES.join(', ')}`)
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      setLog(e.target.result)
      setUploadedFile(file.name)
      setError(null)
    }
    reader.readAsText(file)
  }

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file) readFile(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) readFile(file)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function handleDragLeave() {
    setDragging(false)
  }

  async function handleSubmit() {
    if (!log.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await analyseAlert(log, source)
      navigate(`/incidents/${result.incident_id}`, { state: result })
    } catch (e) {
      setError('analysis failed — check backend connection')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Analyse</div>
          <div className="page-subtitle">submit a log or alert for autonomous analysis</div>
        </div>
      </div>

      <div className="page-body">
        <div className="card">
          <div className="card-header">
            <span className="card-title">input</span>
            {/*toggle between text and file*/}
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                className={`btn ${inputMode === 'text' ? 'btn--primary' : 'btn--ghost'}`}
                style={{ fontSize: '11px', padding: '4px 12px' }}
                onClick={() => { setInputMode('text'); setUploadedFile(null) }}
              >
                paste text
              </button>
              <button
                className={`btn ${inputMode === 'file' ? 'btn--primary' : 'btn--ghost'}`}
                style={{ fontSize: '11px', padding: '4px 12px' }}
                onClick={() => setInputMode('file')}
              >
                upload file
              </button>
            </div>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/*source selector*/}
            <div>
              <div className="input-label">source</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {['manual', 'siem', 'endpoint', 'network'].map(s => (
                  <button
                    key={s}
                    className={`btn ${source === s ? 'btn--primary' : 'btn--ghost'}`}
                    style={{ fontSize: '11px', padding: '4px 12px' }}
                    onClick={() => setSource(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/*text mode*/}
            {inputMode === 'text' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div className="input-label">log or alert</div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {sampleLogs.map(s => (
                      <button
                        key={s.label}
                        className="btn btn--ghost"
                        style={{ fontSize: '11px', padding: '3px 8px' }}
                        onClick={() => setLog(s.log)}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
                <textarea
                  className="textarea"
                  rows={10}
                  placeholder="paste raw log, alert, or suspicious activity here..."
                  value={log}
                  onChange={e => setLog(e.target.value)}
                />
              </div>
            )}

            {/*file upload mode*/}
            {inputMode === 'file' && (
              <div>
                <div className="input-label" style={{ marginBottom: '8px' }}>upload file</div>
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => fileRef.current.click()}
                  style={{
                    border: `1.5px dashed ${dragging ? 'var(--accent-blue)' : 'var(--border-bright)'}`,
                    borderRadius: '4px',
                    padding: '40px 24px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    background: dragging ? 'var(--accent-blue-dim)' : 'var(--bg-base)',
                    transition: 'all 0.15s',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept={ACCEPTED_TYPES.join(',')}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                  {uploadedFile ? (
                    <>
                      <div style={{ fontSize: '24px' }}>✓</div>
                      <div style={{
                        fontSize: '13px',
                        color: 'var(--green)',
                        fontFamily: 'JetBrains Mono, monospace'
                      }}>
                        {uploadedFile}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        click to replace
                      </div>
                    </>
                  ) : (
                    <>
                      <div style={{ fontSize: '24px', color: 'var(--text-muted)' }}>↑</div>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        drop file here or click to browse
                      </div>
                      <div style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        fontFamily: 'JetBrains Mono, monospace'
                      }}>
                        accepted: {ACCEPTED_TYPES.join('  ')}
                      </div>
                    </>
                  )}
                </div>

                {/*preview uploaded content*/}
                {uploadedFile && log && (
                  <div style={{ marginTop: '12px' }}>
                    <div className="input-label" style={{ marginBottom: '8px' }}>preview</div>
                    <textarea
                      className="textarea"
                      rows={6}
                      value={log}
                      onChange={e => setLog(e.target.value)}
                      style={{ fontSize: '11px' }}
                    />
                  </div>
                )}
              </div>
            )}

            {/*error*/}
            {error && (
              <div style={{
                padding: '10px 14px',
                background: 'var(--red-dim)',
                border: '1px solid var(--red)',
                borderRadius: '4px',
                color: 'var(--red)',
                fontSize: '13px',
                fontFamily: 'JetBrains Mono, monospace'
              }}>
                {error}
              </div>
            )}

            {/*loading*/}
            {loading && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="loading-bar">
                  <div className="loading-bar-fill" />
                </div>
                <div style={{
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  running pipeline — triage → investigation → response → report
                </div>
              </div>
            )}

            {/*submit*/}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn--primary"
                onClick={handleSubmit}
                disabled={loading || !log.trim()}
              >
                {loading ? 'analysing...' : 'run analysis →'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}