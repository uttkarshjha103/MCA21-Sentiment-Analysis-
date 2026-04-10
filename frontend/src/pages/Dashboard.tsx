import { useEffect, useState } from 'react'
import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import api from '../api'

ChartJS.register(ArcElement, Tooltip, Legend)

interface Stats {
  total_comments: number
  sentiment_distribution: Record<string, number>
  average_confidence: number
}

interface Comment {
  _id: string
  comment_text: string
  source: string
  date_submitted: string
  sentiment?: { label: string; confidence_score: number }
}

const badge = (label: string) => {
  if (label === 'positive') return 'bg-green-100 text-green-700'
  if (label === 'negative') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-600'
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recent, setRecent] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      const [s, r] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/recent?limit=8'),
      ])
      setStats(s.data)
      setRecent(r.data.comments || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const dist = stats?.sentiment_distribution || {}
  const total = stats?.total_comments || 0

  const chartData = {
    labels: ['Positive', 'Negative', 'Neutral'],
    datasets: [{
      data: [dist.positive || 0, dist.negative || 0, dist.neutral || 0],
      backgroundColor: ['#22c55e', '#ef4444', '#94a3b8'],
      borderWidth: 0,
    }]
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
        <button onClick={load} className="text-sm text-blue-600 hover:underline">↻ Refresh</button>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Total Comments</p>
              <p className="text-3xl font-bold text-gray-800">{total}</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Positive</p>
              <p className="text-3xl font-bold text-green-600">{dist.positive || 0}</p>
              <p className="text-xs text-gray-400 mt-1">{total > 0 ? (((dist.positive || 0) / total) * 100).toFixed(0) : 0}% of total</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Negative</p>
              <p className="text-3xl font-bold text-red-500">{dist.negative || 0}</p>
              <p className="text-xs text-gray-400 mt-1">{total > 0 ? (((dist.negative || 0) / total) * 100).toFixed(0) : 0}% of total</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Avg Confidence</p>
              <p className="text-3xl font-bold text-blue-600">{((stats?.average_confidence || 0) * 100).toFixed(1)}%</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Chart */}
            {total > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border">
                <h3 className="font-semibold text-gray-700 mb-4 text-sm">Sentiment Distribution</h3>
                <Doughnut data={chartData} options={{ plugins: { legend: { position: 'bottom' } } }} />
              </div>
            )}

            {/* Sentiment breakdown bars */}
            {total > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border md:col-span-2">
                <h3 className="font-semibold text-gray-700 mb-5 text-sm">Breakdown</h3>
                <div className="space-y-4">
                  {[
                    { label: 'Positive', count: dist.positive || 0, color: 'bg-green-500' },
                    { label: 'Negative', count: dist.negative || 0, color: 'bg-red-500' },
                    { label: 'Neutral', count: dist.neutral || 0, color: 'bg-gray-400' },
                  ].map(item => (
                    <div key={item.label}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">{item.label}</span>
                        <span className="font-medium text-gray-700">{item.count} ({total > 0 ? ((item.count / total) * 100).toFixed(1) : 0}%)</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2.5">
                        <div className={`h-2.5 rounded-full ${item.color}`} style={{ width: `${total > 0 ? (item.count / total) * 100 : 0}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recent comments */}
          {recent.length > 0 ? (
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="px-6 py-4 border-b">
                <h3 className="font-semibold text-gray-700 text-sm">Recent Comments</h3>
              </div>
              <div className="divide-y">
                {recent.map((c, i) => (
                  <div key={i} className="px-6 py-4 flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-700 line-clamp-2">{c.comment_text}</p>
                      <p className="text-xs text-gray-400 mt-1">{c.source} · {c.date_submitted ? new Date(c.date_submitted).toLocaleDateString() : ''}</p>
                    </div>
                    {c.sentiment?.label && (
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize shrink-0 ${badge(c.sentiment.label)}`}>
                        {c.sentiment.label}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-blue-700 text-sm">
              No comments yet. Go to <strong>Upload</strong> and upload the sample CSV file to see the dashboard populate.
            </div>
          )}
        </>
      )}
    </div>
  )
}
