import { useState } from 'react'
import api from '../api'

interface SentimentResult { label: string; confidence: number; scores: Record<string, number>; processed_at: string }
interface KeywordResult { text: string; tfidf_score: number; frequency: number }

const labelStyle = (l: string) =>
  l === 'positive' ? 'bg-green-100 text-green-700 border-green-200' :
  l === 'negative' ? 'bg-red-100 text-red-700 border-red-200' :
  'bg-gray-100 text-gray-600 border-gray-200'

const labelEmoji = (l: string) => l === 'positive' ? '😊' : l === 'negative' ? '😞' : '😐'

const SAMPLES = [
  { label: 'Positive example', text: 'The new MCA21 corporate governance framework is excellent. It will greatly improve transparency and accountability for all stakeholders. I strongly support this initiative.' },
  { label: 'Negative example', text: 'This regulation imposes unreasonable compliance burden on small businesses. The penalties are too harsh and the implementation timeline is completely unrealistic.' },
  { label: 'Neutral example', text: 'The Ministry has released draft amendments covering board composition, audit requirements, and disclosure norms. The consultation period runs until March 31.' },
]

export default function Analyze() {
  const [text, setText] = useState('')
  const [sentiment, setSentiment] = useState<SentimentResult | null>(null)
  const [keywords, setKeywords] = useState<KeywordResult[]>([])
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'sentiment' | 'keywords'>('sentiment')
  const [history, setHistory] = useState<Array<{ text: string; result: SentimentResult }>>([])

  const analyze = async () => {
    if (!text.trim()) return
    setLoading(true)
    try {
      if (tab === 'sentiment') {
        const { data } = await api.post('/sentiment/analyze', { text })
        setSentiment(data)
        setHistory(h => [{ text: text.slice(0, 80) + (text.length > 80 ? '...' : ''), result: data }, ...h.slice(0, 4)])
      } else {
        const { data } = await api.post('/keywords/analyze', { texts: [text] })
        setKeywords(data.tfidf_keywords || [])
      }
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Analyze Text</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {/* Input card */}
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex gap-2 mb-4">
              {(['sentiment', 'keywords'] as const).map(t => (
                <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{t}</button>
              ))}
            </div>
            <textarea
              className="w-full border rounded-lg p-3 h-36 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="Paste a consultation comment here..."
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <div className="flex items-center justify-between mt-3">
              <span className="text-xs text-gray-400">{text.length} characters</span>
              <button
                onClick={analyze}
                disabled={loading || !text.trim()}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm"
              >
                {loading ? 'Analyzing...' : '🔍 Analyze'}
              </button>
            </div>
          </div>

          {/* Sample texts */}
          <div className="bg-white rounded-xl p-4 shadow-sm border">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Try a sample</p>
            <div className="space-y-2">
              {SAMPLES.map((s, i) => (
                <button key={i} onClick={() => { setText(s.text); setSentiment(null) }}
                  className="w-full text-left text-xs text-gray-600 bg-gray-50 hover:bg-blue-50 hover:text-blue-700 px-3 py-2 rounded-lg transition-colors border border-transparent hover:border-blue-200">
                  <span className="font-medium">{s.label}:</span> {s.text.slice(0, 70)}...
                </button>
              ))}
            </div>
          </div>

          {/* Result */}
          {tab === 'sentiment' && sentiment && (
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="font-semibold text-gray-700 mb-4 text-sm">Sentiment Result</h3>
              <div className="flex items-center gap-4 mb-5">
                <span className="text-4xl">{labelEmoji(sentiment.label)}</span>
                <div>
                  <span className={`inline-block px-4 py-1.5 rounded-full font-bold text-sm capitalize border ${labelStyle(sentiment.label)}`}>{sentiment.label}</span>
                  <p className="text-gray-500 text-sm mt-1">Confidence: <span className="font-semibold text-gray-700">{(sentiment.confidence * 100).toFixed(1)}%</span></p>
                </div>
              </div>
              <div className="space-y-2">
                {Object.entries(sentiment.scores).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-3">
                    <span className="w-20 text-xs text-gray-500 capitalize">{k}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div className={`h-2 rounded-full ${k === 'positive' ? 'bg-green-500' : k === 'negative' ? 'bg-red-500' : 'bg-gray-400'}`} style={{ width: `${(v as number) * 100}%` }} />
                    </div>
                    <span className="text-xs text-gray-500 w-10 text-right">{((v as number) * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === 'keywords' && keywords.length > 0 && (
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="font-semibold text-gray-700 mb-4 text-sm">Extracted Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw, i) => (
                  <span key={i} style={{ fontSize: `${Math.max(11, Math.min(18, 11 + kw.tfidf_score * 8))}px` }}
                    className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium border border-blue-100">
                    {kw.text}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* History sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <h3 className="font-semibold text-gray-700 mb-4 text-sm">Recent Analyses</h3>
            {history.length === 0 ? (
              <p className="text-xs text-gray-400">No analyses yet. Try analyzing a comment.</p>
            ) : (
              <div className="space-y-3">
                {history.map((h, i) => (
                  <div key={i} className="border rounded-lg p-3 cursor-pointer hover:bg-gray-50" onClick={() => setText(h.text)}>
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${labelStyle(h.result.label)}`}>{h.result.label}</span>
                      <span className="text-xs text-gray-400">{(h.result.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-2">{h.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
            <h3 className="font-semibold text-blue-800 mb-2 text-sm">How it works</h3>
            <p className="text-xs text-blue-700 leading-relaxed">
              Uses <strong>RoBERTa</strong> — a transformer AI model trained on millions of texts — to classify public consultation comments as positive, negative, or neutral toward a policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
