import { useState } from 'react'
import api from '../api'

const LENGTHS = [
  { key: 'short', label: 'Short', desc: '~60 words', color: 'bg-yellow-100 text-yellow-700' },
  { key: 'medium', label: 'Medium', desc: '~150 words', color: 'bg-blue-100 text-blue-700' },
  { key: 'long', label: 'Long', desc: '~300 words', color: 'bg-purple-100 text-purple-700' },
]

export default function Summarize() {
  const [texts, setTexts] = useState('')
  const [length, setLength] = useState('medium')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const summarize = async () => {
    const lines = texts.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await api.post('/summarization/generate/by-length', { texts: lines, length })
      setResult(data)
    } catch (e: any) {
      setResult({ error: e.response?.data?.detail || 'Summarization failed' })
    }
    setLoading(false)
  }

  const regenerate = async () => {
    const lines = texts.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length || !result) return
    setLoading(true)
    try {
      const { data } = await api.post('/summarization/regenerate', {
        texts: lines,
        max_length: length === 'short' ? 60 : length === 'long' ? 300 : 150,
        min_length: length === 'short' ? 20 : length === 'long' ? 80 : 40,
      })
      setResult(data)
    } catch (e: any) {
      setResult({ error: e.response?.data?.detail || 'Failed' })
    }
    setLoading(false)
  }

  const lineCount = texts.split('\n').filter(l => l.trim()).length

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">Text Summarization</h2>
      <p className="text-gray-500 text-sm mb-6">Paste multiple comments (one per line) and get an AI-generated summary using the T5 model.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <label className="text-sm font-medium text-gray-700 mb-2 block">Comments (one per line)</label>
            <textarea
              className="w-full border rounded-lg p-3 h-48 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
              placeholder={`The new policy is excellent and will improve transparency.\nThis regulation is too burdensome for small businesses.\nThe consultation process has been inclusive and fair.`}
              value={texts}
              onChange={e => setTexts(e.target.value)}
            />
            <p className="text-xs text-gray-400 mt-1">{lineCount} comment{lineCount !== 1 ? 's' : ''} entered</p>

            <div className="mt-4">
              <label className="text-sm font-medium text-gray-700 mb-2 block">Summary Length</label>
              <div className="flex gap-2">
                {LENGTHS.map(l => (
                  <button key={l.key} onClick={() => setLength(l.key)}
                    className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium border-2 transition-all ${length === l.key ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'}`}>
                    <div className="font-semibold">{l.label}</div>
                    <div className="text-gray-400">{l.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={summarize}
                disabled={loading || !texts.trim()}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm"
              >
                {loading ? 'Summarizing...' : '✨ Generate Summary'}
              </button>
              {result && !result.error && (
                <button onClick={regenerate} disabled={loading} className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50">
                  ↻ Regenerate
                </button>
              )}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl p-5 border border-purple-100">
            <h3 className="font-semibold text-purple-800 mb-2 text-sm">How T5 Summarization works</h3>
            <p className="text-xs text-purple-700 leading-relaxed">
              <strong>T5 (Text-to-Text Transfer Transformer)</strong> by Google reads all the comments together and generates a coherent summary that captures the key themes and opinions. It's trained on millions of documents and understands context deeply.
            </p>
          </div>
        </div>

        <div>
          {result?.error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm">{result.error}</div>
          )}
          {result && !result.error && (
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700 text-sm">Generated Summary</h3>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${LENGTHS.find(l => l.key === length)?.color}`}>
                  {LENGTHS.find(l => l.key === length)?.label}
                </span>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed bg-gray-50 rounded-lg p-4 border">
                {result.summary_text}
              </p>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-lg font-bold text-gray-800">{lineCount}</p>
                  <p className="text-xs text-gray-400">Comments</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-lg font-bold text-gray-800">{result.original_length}</p>
                  <p className="text-xs text-gray-400">Orig. chars</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-lg font-bold text-blue-600">{result.summary_length}</p>
                  <p className="text-xs text-gray-400">Summary chars</p>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-3">Model: {result.model_version} · {new Date(result.generated_at).toLocaleTimeString()}</p>
            </div>
          )}

          {!result && (
            <div className="bg-gray-50 rounded-xl p-8 border-2 border-dashed border-gray-200 text-center">
              <p className="text-4xl mb-3">✨</p>
              <p className="text-gray-500 text-sm">Enter comments on the left and click Generate Summary to see the AI-powered summary here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
