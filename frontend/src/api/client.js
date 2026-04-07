import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Attach JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('arthaai_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Chat ──────────────────────────────────────────────────────

export const sendMessage = (messages, profile, stream = false) =>
  api.post('/chat', { messages, profile, stream })

// Streaming version using fetch (SSE)
export const sendMessageStream = async (messages, profile, onToken, onDone) => {
  const token = localStorage.getItem('arthaai_token')
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages, profile, stream: true }),
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value)
    for (const line of chunk.split('\n')) {
      if (line.startsWith('data: ')) {
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') { onDone?.(); return }
        try {
          const parsed = JSON.parse(raw)
          if (parsed.token) onToken(parsed.token)
        } catch {}
      }
    }
  }
  onDone?.()
}

export const getConversations = () => api.get('/conversations')

// ── Voice ─────────────────────────────────────────────────────

export const transcribeAudio = (audioBlob, language = 'en') => {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.webm')
  form.append('language', language)
  return api.post('/voice/transcribe', form, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export const speakText = async (text, language = 'en') => {
  const res = await fetch('/api/voice/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  })
  if (!res.ok) throw new Error('TTS failed')
  const blob = await res.blob()
  return URL.createObjectURL(blob)
}

// ── Export ────────────────────────────────────────────────────

export const exportPDF = (messages, title, profile) =>
  api.post('/export/pdf', { messages, title, profile }, { responseType: 'blob' })

export const exportExcel = (messages, profile) =>
  api.post('/export/excel', { messages, profile }, { responseType: 'blob' })

export const getWhatsAppLink = (messages, phone = '') =>
  api.post('/export/whatsapp', { messages, phone })

// ── Admin ─────────────────────────────────────────────────────

export const adminLogin = (username, password) =>
  api.post('/admin/login', { username, password })

export const uploadFile = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/admin/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total)),
  })
}

export const triggerScrape = (sources = 'all') =>
  api.post('/admin/scrape', { sources })

export const triggerRetrain = () =>
  api.post('/admin/retrain')

export const getTrainingStatus = () =>
  api.get('/admin/status')

export const listFiles = () =>
  api.get('/admin/files')

export const deleteFile = (filename) =>
  api.delete(`/admin/files/${filename}`)

export const getPublicStats = () =>
  api.get('/stats')

export default api
