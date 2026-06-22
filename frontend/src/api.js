// 统一的后端调用封装。所有请求走 /api，由 Vite 代理转发到后端（见 vite.config.js）。
const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json()
}

export const api = {
  // 上传音频，返回 { id, status, ... }
  upload(file) {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/meetings`, { method: 'POST', body: form }).then(handle)
  },
  listMeetings() {
    return fetch(`${BASE}/meetings`).then(handle)
  },
  getMeeting(id) {
    return fetch(`${BASE}/meetings/${id}`).then(handle)
  },
  getExtraction(id) {
    // 抽取异步生成，可能 404（还没好）
    return fetch(`${BASE}/meetings/${id}/extraction`).then(handle)
  },
  listTodos(meetingId) {
    const q = meetingId ? `?meeting_id=${meetingId}` : ''
    return fetch(`${BASE}/todos${q}`).then(handle)
  },
  search(q, topK = 5) {
    return fetch(`${BASE}/search?q=${encodeURIComponent(q)}&top_k=${topK}`).then(handle)
  },
}
