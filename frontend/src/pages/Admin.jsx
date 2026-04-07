import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { adminLogin, uploadFile, triggerScrape, triggerRetrain,
         getTrainingStatus, listFiles, deleteFile } from '../api/client'

export default function Admin() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('arthaai_token'))
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const [status, setStatus] = useState(null)
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef()
  const pollRef = useRef()

  useEffect(() => {
    if (isLoggedIn) {
      fetchStatus()
      fetchFiles()
      pollRef.current = setInterval(fetchStatus, 4000)
    }
    return () => clearInterval(pollRef.current)
  }, [isLoggedIn])

  const fetchStatus = async () => {
    try { const { data } = await getTrainingStatus(); setStatus(data) } catch {}
  }

  const fetchFiles = async () => {
    try { const { data } = await listFiles(); setFiles(data.files || []) } catch {}
  }

  const handleLogin = async () => {
    try {
      const { data } = await adminLogin(credentials.username, credentials.password)
      localStorage.setItem('arthaai_token', data.access_token)
      setIsLoggedIn(true)
      toast.success('Admin login successful')
    } catch { toast.error('Invalid credentials') }
  }

  const handleUpload = async (file) => {
    if (!file) return
    setUploading(true)
    setUploadProgress(0)
    try {
      const { data } = await uploadFile(file, setUploadProgress)
      toast.success(`✅ ${data.filename} — ${data.chunks_added} chunks added`)
      fetchFiles(); fetchStatus()
    } catch (e) {
      toast.error(`Upload failed: ${e.response?.data?.error || e.message}`)
    } finally { setUploading(false); setUploadProgress(0) }
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  const handleScrape = async () => {
    const id = toast.loading('Starting web scraping...')
    try { await triggerScrape(); toast.success('Scraping started in background', { id }) }
    catch { toast.error('Scrape trigger failed', { id }) }
  }

  const handleRetrain = async () => {
    const id = toast.loading('Retraining model...')
    try { await triggerRetrain(); toast.success('Retraining started', { id }); fetchStatus() }
    catch { toast.error('Retrain failed', { id }) }
  }

  const handleDelete = async (fname) => {
    if (!confirm(`Delete ${fname}?`)) return
    try { await deleteFile(fname); toast.success(`${fname} deleted`); fetchFiles() }
    catch { toast.error('Delete failed') }
  }

  // ── Login screen ──────────────────────────────────────────
  if (!isLoggedIn) return (
    <div style={styles.loginWrap}>
      <div style={styles.loginCard}>
        <div style={styles.loginLogo}>🏛️</div>
        <h2 style={styles.loginTitle}>Admin Panel</h2>
        <p style={styles.loginSub}>ArthaAI — Model Training Dashboard</p>
        {['username', 'password'].map(field => (
          <input key={field} type={field} placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
            value={credentials[field]}
            onChange={e => setCredentials(p => ({ ...p, [field]: e.target.value }))}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            style={styles.loginInput}
          />
        ))}
        <button style={styles.loginBtn} onClick={handleLogin}>Login →</button>
      </div>
    </div>
  )

  // ── Admin dashboard ───────────────────────────────────────
  const rag = status?.rag_stats || {}
  const progress = status?.progress || {}

  return (
    <div style={styles.adminWrap}>
      <div style={styles.adminHeader}>
        <div>
          <div style={styles.adminTitle}>Training Dashboard</div>
          <div style={styles.adminSub}>Manage data sources, upload files, retrain the RAG model</div>
        </div>
        <button style={styles.logoutBtn} onClick={() => { localStorage.removeItem('arthaai_token'); setIsLoggedIn(false) }}>
          Logout
        </button>
      </div>

      {/* Stats row */}
      <div style={styles.statsRow}>
        {[
          ['Total Chunks', rag.total_chunks ?? '—', 'Knowledge base size'],
          ['Data Sources', Object.keys(rag.sources || {}).length, 'Unique sources indexed'],
          ['Index Size', rag.index_size ?? '—', 'FAISS vector entries'],
          ['Last Trained', status?.last_trained ? new Date(status.last_trained).toLocaleTimeString('en-IN') : '—', 'IST'],
        ].map(([label, val, sub]) => (
          <div key={label} style={styles.statCard}>
            <div style={styles.statLabel}>{label}</div>
            <div style={styles.statVal}>{String(val)}</div>
            <div style={styles.statSub}>{sub}</div>
          </div>
        ))}
      </div>

      <div style={styles.grid}>
        {/* Upload */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>📁 Upload Training Data</div>
          <div
            style={{ ...styles.dropzone, borderColor: dragOver ? '#FF6B00' : 'var(--color-border-tertiary)', background: dragOver ? '#FFF0E6' : 'transparent' }}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div style={styles.dropIcon}>⬆</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
              {uploading ? `Uploading... ${uploadProgress}%` : 'Drop files here or click to browse'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', marginTop: 4 }}>
              PDF, CSV, Excel, JSON, TXT — Max 500MB
            </div>
            {uploading && (
              <div style={styles.progressBar}>
                <div style={{ ...styles.progressFill, width: `${uploadProgress}%` }} />
              </div>
            )}
          </div>
          <input ref={fileInputRef} type="file" style={{ display: 'none' }}
            accept=".pdf,.csv,.xlsx,.xls,.json,.txt,.md"
            onChange={e => handleUpload(e.target.files[0])} />
        </div>

        {/* Live data sources */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>🌐 Live Data Sources</div>
          <div style={styles.sourceGrid}>
            {[
              ['RBI', 'Policy rates, circulars', true],
              ['NSE/BSE', 'Market indices, stocks', true],
              ['AMFI', 'Mutual fund NAVs', true],
              ['MCX', 'Gold & silver prices', true],
              ['SEBI', 'Investor circulars', false],
              ['Govt Budget', 'Union budget PDFs', false],
            ].map(([name, desc, live]) => (
              <div key={name} style={styles.sourceCard}>
                <div style={styles.sourceName}>{name}</div>
                <div style={styles.sourceDesc}>{desc}</div>
<div 
  style={{ 
    ...styles.sourceBadge, 
    background: live ? '#E1F5EE' : '#FFF0E6', 
    color: live ? '#0F6E56' : '#7A5010' 
  }}
>
                  {live ? '● Live' : '○ Pending'}
                </div>
              </div>
            ))}
          </div>
          <button style={styles.scrapeBtn} onClick={handleScrape}>
            ↓ Fetch Latest Data
          </button>
        </div>
      </div>

      {/* Training status */}
      <div style={styles.section}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={styles.sectionTitle}>⚡ Model Training</div>
          <button style={styles.trainBtn} onClick={handleRetrain} disabled={status?.is_training}>
            {status?.is_training ? '⏳ Training...' : '⚡ Retrain Now'}
          </button>
        </div>
        <div style={styles.progressList}>
          {[
            ['File Ingestion', progress.files],
            ['Web Scraping', progress.scraping],
            ['Embedding', progress.embedding],
            ['FAISS Index', progress.faiss_index],
          ].map(([label, val]) => (
            <div key={label} style={styles.progressRow}>
              <div style={styles.progLabel}>{label}</div>
              <div style={styles.progBarWrap}>
                <div style={{ ...styles.progBarFill, width: val?.includes('done') || val === 'done' ? '100%' : val?.includes('running') ? '50%' : '0%', background: val?.includes('error') ? '#E24B4A' : '#FF6B00' }} />
              </div>
              <div style={styles.progStatus}>{val || '—'}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Uploaded files */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>📂 Uploaded Files ({files.length})</div>
        {files.length === 0
          ? <div style={{ fontSize: 13, color: 'var(--color-text-tertiary)', padding: '20px 0' }}>No files uploaded yet.</div>
          : <div style={styles.fileList}>
              {files.map(f => (
                <div key={f.name} style={styles.fileRow}>
                  <div style={styles.fileIcon}>{f.type === 'PDF' ? '📄' : f.type === 'CSV' ? '📊' : '📁'}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: 'var(--color-text-primary)' }}>{f.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>{f.type} · {f.size_kb} KB</div>
                  </div>
                  <button style={styles.deleteBtn} onClick={() => handleDelete(f.name)}>✕</button>
                </div>
              ))}
            </div>
        }
      </div>

      {/* Source breakdown */}
      {rag.sources && Object.keys(rag.sources).length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>📊 Knowledge Base Breakdown</div>
          <div style={styles.fileList}>
            {Object.entries(rag.sources).sort((a, b) => b[1] - a[1]).map(([src, count]) => (
              <div key={src} style={{ ...styles.fileRow, padding: '8px 0' }}>
                <div style={{ flex: 1, fontSize: 13, color: 'var(--color-text-secondary)' }}>{src}</div>
                <div style={{ fontSize: 12, fontFamily: 'monospace', color: '#FF6B00' }}>{count} chunks</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  loginWrap: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' },
  loginCard: { width: 340, padding: 32, border: '0.5px solid var(--color-border-tertiary)', borderRadius: 16, display: 'flex', flexDirection: 'column', gap: 12, background: 'var(--color-background-primary)' },
  loginLogo: { fontSize: 36, textAlign: 'center' },
  loginTitle: { fontSize: 20, fontWeight: 500, color: 'var(--color-text-primary)', textAlign: 'center' },
  loginSub: { fontSize: 12, color: 'var(--color-text-tertiary)', textAlign: 'center', marginBottom: 8 },
  loginInput: { padding: '10px 14px', borderRadius: 8, border: '0.5px solid var(--color-border-tertiary)', fontSize: 13, background: 'var(--color-background-secondary)', color: 'var(--color-text-primary)', outline: 'none' },
  loginBtn: { padding: '11px', borderRadius: 8, background: '#FF6B00', color: 'white', border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 500 },
  adminWrap: { padding: 20, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 20 },
  adminHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  adminTitle: { fontSize: 16, fontWeight: 500, color: 'var(--color-text-primary)' },
  adminSub: { fontSize: 12, color: 'var(--color-text-tertiary)', marginTop: 2 },
  logoutBtn: { fontSize: 12, padding: '6px 14px', borderRadius: 6, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', color: 'var(--color-text-secondary)', cursor: 'pointer' },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 10 },
  statCard: { background: 'var(--color-background-secondary)', borderRadius: 10, padding: '12px 14px' },
  statLabel: { fontSize: 10, fontWeight: 600, color: 'var(--color-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  statVal: { fontSize: 22, fontWeight: 500, color: 'var(--color-text-primary)', fontFamily: 'monospace', marginTop: 4 },
  statSub: { fontSize: 11, color: 'var(--color-text-tertiary)', marginTop: 2 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  section: { border: '0.5px solid var(--color-border-tertiary)', borderRadius: 12, padding: 16 },
  sectionTitle: { fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)', marginBottom: 12 },
  dropzone: { border: '1.5px dashed', borderRadius: 10, padding: '28px 20px', textAlign: 'center', cursor: 'pointer', transition: 'all 0.15s' },
  dropIcon: { fontSize: 28, marginBottom: 8, color: 'var(--color-text-tertiary)' },
  progressBar: { height: 6, background: 'var(--color-background-secondary)', borderRadius: 99, marginTop: 12, overflow: 'hidden' },
  progressFill: { height: '100%', background: '#FF6B00', borderRadius: 99, transition: 'width 0.3s' },
  sourceGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 10 },
  sourceCard: { padding: '10px', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 8, background: 'var(--color-background-secondary)' },
  sourceName: { fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' },
  sourceDesc: { fontSize: 10, color: 'var(--color-text-tertiary)', marginTop: 2 },
  sourceBadge: { fontSize: 9, padding: '2px 7px', borderRadius: 99, display: 'inline-block', marginTop: 5 },
  scrapeBtn: { fontSize: 12, padding: '7px 16px', borderRadius: 7, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', color: 'var(--color-text-secondary)', cursor: 'pointer', width: '100%' },
  trainBtn: { fontSize: 13, padding: '8px 18px', borderRadius: 8, background: '#0D1B3E', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 500 },
  progressList: { display: 'flex', flexDirection: 'column', gap: 8 },
  progressRow: { display: 'flex', alignItems: 'center', gap: 10 },
  progLabel: { width: 110, fontSize: 12, color: 'var(--color-text-secondary)', flexShrink: 0 },
  progBarWrap: { flex: 1, height: 6, borderRadius: 99, background: 'var(--color-background-secondary)', overflow: 'hidden' },
  progBarFill: { height: '100%', borderRadius: 99, transition: 'width 0.4s' },
  progStatus: { width: 80, fontSize: 11, color: 'var(--color-text-tertiary)', textAlign: 'right', fontFamily: 'monospace' },
  fileList: { display: 'flex', flexDirection: 'column', gap: 4 },
  fileRow: { display: 'flex', alignItems: 'center', gap: 10, padding: '8px 4px', borderBottom: '0.5px solid var(--color-border-tertiary)' },
  fileIcon: { fontSize: 18 },
  deleteBtn: { fontSize: 12, padding: '3px 8px', borderRadius: 5, border: 'none', background: '#FCEBEB', color: '#A32D2D', cursor: 'pointer' },
}
