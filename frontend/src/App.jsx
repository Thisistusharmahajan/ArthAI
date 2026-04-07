import { useState } from 'react'
import { Toaster } from 'react-hot-toast'
import Chat from './pages/Chat'
import Admin from './pages/Admin'
import './index.css'

const NAV_ITEMS = [
  { id: 'chat', label: 'Advisor Chat', icon: '💬', desc: 'AI-powered advice' },
  { id: 'admin', label: 'Admin Panel', icon: '⚙️', desc: 'Train & manage data' },
]

const CATEGORIES = [
  { icon: '📈', label: 'Mutual Funds' },
  { icon: '🏦', label: 'Bank FDs' },
  { icon: '📊', label: 'Stocks & ETFs' },
  { icon: '🥇', label: 'Gold & Silver' },
  { icon: '🛡️', label: 'Insurance' },
  { icon: '🏠', label: 'Real Estate' },
  { icon: '💰', label: 'Tax Planning' },
  { icon: '🎯', label: 'SIP Calculator' },
]

export default function App() {
  const [page, setPage] = useState('chat')
  const [activeCategory, setActiveCategory] = useState(null)

  return (
    <div style={styles.app}>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />

      {/* Top bar */}
      <div style={styles.topbar}>
        <div style={styles.logo}>
          <div style={styles.logoIcon}>
            <span style={{ fontSize: 16 }}>₹</span>
          </div>
          <div>
            <div style={styles.logoName}>
              Artha<span style={{ color: '#FF6B00' }}>AI</span>
            </div>
            <div style={styles.logoSub}>Indian Budget & Investment Analyzer</div>
          </div>
        </div>

        <div style={styles.navTabs}>
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              style={{ ...styles.navTab, ...(page === item.id ? styles.navTabActive : {}) }}
              onClick={() => setPage(item.id)}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>

        <div style={styles.userBadge}>
          <div style={styles.userAvatar}>RK</div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>Rahul Kumar</div>
            <div style={{ fontSize: 10, color: 'var(--color-text-tertiary)' }}>Upper Middle Class</div>
          </div>
        </div>
      </div>

      <div style={styles.body}>
        {/* Sidebar — only show on chat page */}
        {page === 'chat' && (
          <div style={styles.sidebar}>
            <div style={styles.sideSection}>
              <div style={styles.sideLabel}>Quick Categories</div>
              {CATEGORIES.map(cat => (
                <button
                  key={cat.label}
                  style={{ ...styles.sideItem, ...(activeCategory === cat.label ? styles.sideItemActive : {}) }}
                  onClick={() => setActiveCategory(cat.label === activeCategory ? null : cat.label)}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.label}</span>
                </button>
              ))}
            </div>

            <div style={styles.profileCard}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>Rahul Kumar</div>
              <div style={styles.classBadge}>Upper Middle Class</div>
              <div style={styles.profileStat}>Income: <strong>₹1,20,000/mo</strong></div>
              <div style={styles.profileStat}>Goal: <strong>₹30,000 savings</strong></div>
              <div style={styles.profileStat}>Risk: <strong>Moderate</strong></div>
            </div>
          </div>
        )}

        {/* Main panel */}
        <div style={styles.main}>
          {page === 'chat' && <Chat categoryFilter={activeCategory} />}
          {page === 'admin' && <Admin />}
        </div>
      </div>
    </div>
  )
}

const styles = {
  app: { display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--color-background-tertiary)', fontFamily: "'Sora', sans-serif" },
  topbar: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-primary)', flexShrink: 0, zIndex: 10 },
  logo: { display: 'flex', alignItems: 'center', gap: 10 },
  logoIcon: { width: 36, height: 36, borderRadius: 8, background: '#FF6B00', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700, fontSize: 18 },
  logoName: { fontSize: 16, fontWeight: 700, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' },
  logoSub: { fontSize: 10, color: 'var(--color-text-tertiary)', letterSpacing: '0.03em' },
  navTabs: { display: 'flex', gap: 4 },
  navTab: { fontSize: 12, padding: '7px 16px', borderRadius: 8, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', color: 'var(--color-text-secondary)', cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500, transition: 'all 0.12s' },
  navTabActive: { background: '#FF6B00', color: 'white', border: '0.5px solid #FF6B00' },
  userBadge: { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 99 },
  userAvatar: { width: 28, height: 28, borderRadius: '50%', background: '#FFF0E6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: '#FF6B00' },
  body: { display: 'flex', flex: 1, minHeight: 0 },
  sidebar: { width: 210, minWidth: 210, borderRight: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-primary)', display: 'flex', flexDirection: 'column', overflowY: 'auto' },
  sideSection: { padding: '14px 10px 8px', display: 'flex', flexDirection: 'column', gap: 2 },
  sideLabel: { fontSize: 10, fontWeight: 600, color: 'var(--color-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 6px', marginBottom: 4 },
  sideItem: { display: 'flex', alignItems: 'center', gap: 8, padding: '7px 8px', borderRadius: 8, border: 'none', background: 'transparent', color: 'var(--color-text-secondary)', fontSize: 12, cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', transition: 'all 0.1s' },
  sideItemActive: { background: '#FFF0E6', color: '#FF6B00', fontWeight: 500 },
  profileCard: { margin: '8px', padding: '12px', borderRadius: 10, border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)', marginTop: 'auto' },
  classBadge: { fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 99, background: '#E1F5EE', color: '#0F6E56', display: 'inline-block', marginTop: 3, marginBottom: 6 },
  profileStat: { fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 3 },
  main: { flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--color-background-primary)', minHeight: 0, overflow: 'hidden' },
}
