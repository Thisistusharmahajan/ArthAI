import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import toast from 'react-hot-toast'
import { sendMessageStream, transcribeAudio, speakText,
         exportPDF, exportExcel, getWhatsAppLink } from '../api/client'

const QUICK_SUGGESTIONS = [
  'Best SIP options for ₹10,000/month',
  'Compare SBI FD vs HDFC FD rates',
  'Should I invest in gold now?',
  'How to save tax under Section 80C?',
  'Best ELSS mutual funds 2025',
  'NPS vs PPF — which is better?',
  'Home loan or rent — what makes sense?',
  'Emergency fund — where to keep it?',
]

const USER_CLASSES = [
  { label: 'Low Income', range: 'Below ₹5L/yr', color: '#1D9E75' },
  { label: 'Middle Class', range: '₹5L–15L/yr', color: '#D4AF37' },
  { label: 'Upper Middle', range: '₹15L–30L/yr', color: '#FF6B00' },
  { label: 'Rich', range: '₹30L–1Cr/yr', color: '#534AB7' },
  { label: 'Super Rich', range: 'Above ₹1Cr/yr', color: '#E24B4A' },
]

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Namaste! 🙏 I'm **ArthaAI**, your personal Indian financial advisor.

I can help you with:
- 📈 **Mutual Funds & SIPs** — Best funds for your profile
- 🏦 **Fixed Deposits** — Current rates from all major banks
- 🥇 **Gold & Silver** — SGB, ETF, or physical?
- 📊 **Stock Market** — Index funds, sectoral, long-term picks
- 🛡️ **Tax Planning** — Save tax under 80C, 80D, and more
- 🏠 **Real Estate** — Buy vs rent, home loan analysis

Tell me about yourself — your income, city, and what you want to achieve financially!`,
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [profile, setProfile] = useState({
    name: '', city: '', profession: '',
    monthly_income: 0, monthly_savings: 0,
    risk_appetite: 'Moderate', investment_goal: ''
  })
  const [showProfile, setShowProfile] = useState(false)
  const [language, setLanguage] = useState('en')

  const bottomRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Send message ──────────────────────────────────────────

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return
    const userMsg = { role: 'user', content: text.trim() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    // Streaming placeholder
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])

    try {
      let fullText = ''
      await sendMessageStream(
        newMessages,
        profile,
        (token) => {
          fullText += token
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: 'assistant', content: fullText, streaming: true }
            return updated
          })
        },
        () => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { role: 'assistant', content: fullText }
            return updated
          })
          setIsLoading(false)
        }
      )
    } catch (err) {
      setMessages(prev => prev.filter(m => !m.streaming))
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}. Please check your API configuration.`
      }])
      setIsLoading(false)
    }
  }, [messages, profile, isLoading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  // ── Voice Input ───────────────────────────────────────────

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data)
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        try {
          const { data } = await transcribeAudio(blob, language)
          if (data.transcript) {
            setInput(data.transcript)
            toast.success('Voice transcribed!')
          }
        } catch {
          toast.error('Transcription failed. Check Whisper setup.')
        }
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
      toast('Recording... tap again to stop', { icon: '🎙️' })
    } catch {
      toast.error('Microphone access denied')
    }
  }

  // ── TTS Output ────────────────────────────────────────────

  const speakLastResponse = async () => {
    const lastAI = [...messages].reverse().find(m => m.role === 'assistant')
    if (!lastAI) return
    setIsSpeaking(true)
    try {
      const url = await speakText(lastAI.content.replace(/[*_#]/g, ''), language)
      if (audioRef.current) audioRef.current.pause()
      audioRef.current = new Audio(url)
      audioRef.current.play()
      audioRef.current.onended = () => setIsSpeaking(false)
    } catch {
      toast.error('Text-to-speech failed. Check gTTS setup.')
      setIsSpeaking(false)
    }
  }

  const stopSpeaking = () => {
    audioRef.current?.pause()
    setIsSpeaking(false)
  }

  // ── Export ────────────────────────────────────────────────

  const handleExportPDF = async () => {
    const toastId = toast.loading('Generating PDF...')
    try {
      const { data } = await exportPDF(messages, 'ArthaAI Consultation', profile)
      const url = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
      const a = document.createElement('a'); a.href = url; a.download = 'ArthaAI_Report.pdf'; a.click()
      toast.success('PDF downloaded!', { id: toastId })
    } catch { toast.error('PDF export failed', { id: toastId }) }
  }

  const handleExportExcel = async () => {
    const toastId = toast.loading('Generating Excel...')
    try {
      const { data } = await exportExcel(messages, profile)
      const url = URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a'); a.href = url; a.download = 'ArthaAI_Consultation.xlsx'; a.click()
      toast.success('Excel downloaded!', { id: toastId })
    } catch { toast.error('Excel export failed', { id: toastId }) }
  }

  const handleWhatsApp = async () => {
    try {
      const { data } = await getWhatsAppLink(messages)
      window.open(data.whatsapp_url, '_blank')
    } catch { toast.error('WhatsApp share failed') }
  }

  // ── Render ────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Chat header */}
      <div style={styles.chatHeader}>
        <div>
          <div style={styles.chatTitle}>Financial Advisor Chat</div>
          <div style={styles.chatSub}>Powered by RAG + live Indian market data</div>
        </div>
        <div style={styles.headerRight}>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            style={styles.langSelect}
          >
            <option value="en">🇬🇧 English</option>
            <option value="hi">🇮🇳 Hindi</option>
          </select>
          <button style={styles.profileBtn} onClick={() => setShowProfile(!showProfile)}>
            👤 Profile
          </button>
        </div>
      </div>

      {/* Profile panel */}
      {showProfile && (
        <div style={styles.profilePanel}>
          <div style={styles.profileGrid}>
            {[
              ['name', 'Your Name', 'text', 'Rahul Kumar'],
              ['city', 'City', 'text', 'Mumbai'],
              ['profession', 'Profession', 'text', 'Software Engineer'],
              ['monthly_income', 'Monthly Income (₹)', 'number', '120000'],
              ['monthly_savings', 'Monthly Savings Target (₹)', 'number', '30000'],
              ['investment_goal', 'Investment Goal', 'text', 'Retirement corpus in 15 years'],
            ].map(([key, label, type, placeholder]) => (
              <div key={key} style={styles.profileField}>
                <label style={styles.profileLabel}>{label}</label>
                <input
                  type={type}
                  value={profile[key]}
                  placeholder={placeholder}
                  onChange={e => setProfile(p => ({ ...p, [key]: type === 'number' ? +e.target.value : e.target.value }))}
                  style={styles.profileInput}
                />
              </div>
            ))}
            <div style={styles.profileField}>
              <label style={styles.profileLabel}>Risk Appetite</label>
              <select
                value={profile.risk_appetite}
                onChange={e => setProfile(p => ({ ...p, risk_appetite: e.target.value }))}
                style={styles.profileInput}
              >
                <option>Low</option>
                <option>Moderate</option>
                <option>High</option>
                <option>Very High</option>
              </select>
            </div>
          </div>
          <button
            style={styles.saveBtn}
            onClick={() => { setShowProfile(false); toast.success('Profile saved! AI will personalize advice.') }}
          >
            Save Profile ✓
          </button>
        </div>
      )}

      {/* Messages */}
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', marginBottom: 16 }}>
            <div style={{
              ...styles.avatar,
              background: msg.role === 'user' ? '#0D1B3E' : '#FF6B00',
              flexShrink: 0,
            }}>
              {msg.role === 'user' ? '👤' : 'A'}
            </div>
            <div style={{
              ...styles.bubble,
              background: msg.role === 'user' ? '#0D1B3E' : 'var(--color-background-secondary)',
              color: msg.role === 'user' ? 'white' : 'var(--color-text-primary)',
              borderTopRightRadius: msg.role === 'user' ? 4 : 14,
              borderTopLeftRadius: msg.role === 'user' ? 14 : 4,
              maxWidth: '75%',
            }}>
              {msg.role === 'assistant'
                ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content || '▋'}</ReactMarkdown>
                : msg.content
              }
              {msg.streaming && <span style={{ opacity: 0.5 }}>▋</span>}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 2 && (
        <div style={styles.suggestions}>
          {QUICK_SUGGESTIONS.map((s, i) => (
            <button key={i} style={styles.chip} onClick={() => sendMessage(s)}>{s}</button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div style={styles.inputArea}>
        <div style={styles.inputWrap}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything — investments, savings, taxes, loans..."
            style={styles.textarea}
            rows={1}
            disabled={isLoading}
          />
          <button
            style={{ ...styles.voiceBtn, background: isRecording ? '#E24B4A' : 'transparent', color: isRecording ? 'white' : 'var(--color-text-secondary)' }}
            onClick={toggleRecording}
            title={isRecording ? 'Stop recording' : 'Voice input'}
          >
            🎙
          </button>
        </div>
        {isSpeaking
          ? <button style={{ ...styles.sendBtn, background: '#E24B4A' }} onClick={stopSpeaking}>⏹</button>
          : <button style={styles.sendBtn} onClick={() => sendMessage(input)} disabled={isLoading || !input.trim()}>
              {isLoading ? '...' : '➤'}
            </button>
        }
        <button style={styles.speakBtn} onClick={speakLastResponse} title="Read last response aloud">🔊</button>
      </div>

      {/* Export bar */}
      <div style={styles.exportBar}>
        <span style={styles.exportLabel}>Export chat:</span>
        <button style={styles.exportBtn} onClick={handleExportPDF}>📄 PDF</button>
        <button style={styles.exportBtn} onClick={handleExportExcel}>📊 Excel</button>
        <button style={{ ...styles.exportBtn, ...styles.waBtn }} onClick={handleWhatsApp}>💬 WhatsApp</button>
        <div style={{ flex: 1 }} />
        <button style={styles.clearBtn} onClick={() => { setMessages([]); toast('Chat cleared') }}>Clear</button>
      </div>
    </div>
  )
}

const styles = {
  chatHeader: { padding: '14px 20px', borderBottom: '0.5px solid var(--color-border-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  chatTitle: { fontSize: 15, fontWeight: 500, color: 'var(--color-text-primary)' },
  chatSub: { fontSize: 11, color: 'var(--color-text-tertiary)', marginTop: 2 },
  headerRight: { display: 'flex', gap: 8, alignItems: 'center' },
  langSelect: { fontSize: 12, padding: '5px 8px', borderRadius: 6, border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)', color: 'var(--color-text-primary)' },
  profileBtn: { fontSize: 12, padding: '6px 12px', borderRadius: 6, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', color: 'var(--color-text-secondary)', cursor: 'pointer' },
  profilePanel: { padding: '16px 20px', borderBottom: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)' },
  profileGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px 16px', marginBottom: 12 },
  profileField: { display: 'flex', flexDirection: 'column', gap: 4 },
  profileLabel: { fontSize: 11, color: 'var(--color-text-secondary)', fontWeight: 500 },
  profileInput: { fontSize: 13, padding: '6px 10px', borderRadius: 6, border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-primary)', color: 'var(--color-text-primary)' },
  saveBtn: { fontSize: 13, padding: '8px 20px', borderRadius: 8, background: '#FF6B00', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 500 },
  messages: { flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', minHeight: 0 },
  avatar: { width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 600, color: 'white' },
  bubble: { padding: '10px 14px', borderRadius: 14, fontSize: 13, lineHeight: 1.6 },
  suggestions: { padding: '0 20px 12px', display: 'flex', flexWrap: 'wrap', gap: 6 },
  chip: { fontSize: 11, padding: '5px 12px', borderRadius: 99, border: '0.5px solid var(--color-border-tertiary)', background: 'var(--color-background-secondary)', color: 'var(--color-text-secondary)', cursor: 'pointer', whiteSpace: 'nowrap' },
  inputArea: { padding: '12px 16px', borderTop: '0.5px solid var(--color-border-tertiary)', display: 'flex', gap: 8, alignItems: 'flex-end' },
  inputWrap: { flex: 1, position: 'relative' },
  textarea: { width: '100%', resize: 'none', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 12, padding: '10px 40px 10px 14px', fontSize: 13, background: 'var(--color-background-secondary)', color: 'var(--color-text-primary)', outline: 'none', fontFamily: 'inherit', lineHeight: 1.5 },
  voiceBtn: { position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', width: 26, height: 26, borderRadius: '50%', border: '0.5px solid var(--color-border-tertiary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12 },
  sendBtn: { width: 42, height: 42, borderRadius: 10, background: '#FF6B00', border: 'none', cursor: 'pointer', color: 'white', fontSize: 16, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  speakBtn: { width: 42, height: 42, borderRadius: 10, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', cursor: 'pointer', fontSize: 18, flexShrink: 0 },
  exportBar: { padding: '8px 16px', borderTop: '0.5px solid var(--color-border-tertiary)', display: 'flex', alignItems: 'center', gap: 6 },
  exportLabel: { fontSize: 11, color: 'var(--color-text-tertiary)' },
  exportBtn: { fontSize: 11, padding: '4px 10px', borderRadius: 6, border: '0.5px solid var(--color-border-tertiary)', background: 'transparent', color: 'var(--color-text-secondary)', cursor: 'pointer' },
  waBtn: { color: '#2E7D32' },
  clearBtn: { fontSize: 11, padding: '4px 10px', borderRadius: 6, border: 'none', background: 'transparent', color: 'var(--color-text-tertiary)', cursor: 'pointer' },
}
