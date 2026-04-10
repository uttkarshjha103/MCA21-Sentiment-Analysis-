import { useEffect, useState } from 'react'
import api from '../api'

interface Comment {
  _id: string
  comment_text: string
  source: string
  date_submitted: string
  original_language?: string
  sentiment?: { label: string; confidence_score: number }
}

const badge = (label: string) =>
  label === 'positive' ? 'bg-green-100 text-green-700' :
  label === 'negative' ? 'bg-red-100 text-red-700' :
  'bg-gray-100 text-gray-500'

export default function Comments() {
  const [comments, setComments] = useState<Comment[]>([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const url = filter ? `/dashboard/recent?limit=50&sentiment=${filter}` : '/dashboard/recent?limit=50'
    api.get(url).then(r => { setComments(r.data.comments || []); setLoading(false) }).catch(() => setLoading(false))
  }, [filter])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Comments</h2>
        <div className="flex gap-2">
          {['', 'positive', 'negative', 'neutral'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
              {f || 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? <p className="text-gray-400 text-sm">Loading...</p> : (
        comments.length === 0 ? (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-blue-700 text-sm">
            No comments found. Upload a CSV file first.
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border divide-y">
            {comments.map((c, i) => (
              <div key={i} className="p-5 flex gap-4 items-start">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 mb-2">{c.comment_text}</p>
                  <div className="flex gap-3 text-xs text-gray-400">
                    <span>📁 {c.source}</span>
                    <span>📅 {c.date_submitted ? new Date(c.date_submitted).toLocaleDateString() : 'N/A'}</span>
                    {c.original_language && <span>🌐 {c.original_language}</span>}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  {c.sentiment?.label ? (
                    <>
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${badge(c.sentiment.label)}`}>{c.sentiment.label}</span>
                      <p className="text-xs text-gray-400 mt-1">{((c.sentiment.confidence_score || 0) * 100).toFixed(0)}% conf.</p>
                    </>
                  ) : (
                    <span className="text-xs text-gray-300">No analysis</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
