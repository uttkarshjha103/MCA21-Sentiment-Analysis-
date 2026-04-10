import { useState } from 'react'
import api from '../api'

export default function Reports() {
  const [title, setTitle] = useState('MCA21 Consultation Analysis Report')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<any>(null)
  const [csvLoading, setCsvLoading] = useState(false)

  const generateExcel = async () => {
    setLoading(true)
    setReport(null)
    try {
      const { data } = await api.post('/reports/excel', { title, report_type: 'excel', include_metadata: true })
      setReport(data)
    } catch (e: any) {
      setReport({ error: e.response?.data?.detail || 'Failed to generate report' })
    }
    setLoading(false)
  }

  const downloadCsv = async () => {
    setCsvLoading(true)
    try {
      const response = await api.get('/reports/export/csv', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `mca21_export_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
    setCsvLoading(false)
  }

  const downloadExcel = async (reportId: string) => {
    try {
      const response = await api.get(`/reports/${reportId}/download`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${reportId}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Reports & Export</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Excel Report */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">📊</span>
            <div>
              <h3 className="font-semibold text-gray-800">Excel Report</h3>
              <p className="text-xs text-gray-400">Full analytics with charts and metadata</p>
            </div>
          </div>
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Report title"
          />
          <button
            onClick={generateExcel}
            disabled={loading}
            className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium text-sm"
          >
            {loading ? 'Generating...' : '⬇ Generate Excel Report'}
          </button>

          {report && !report.error && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-700 font-semibold text-sm mb-1">Report Ready!</p>
              <p className="text-xs text-green-600 mb-3">
                {report.metadata?.total_comments || 0} comments exported
              </p>
              <button
                onClick={() => downloadExcel(report.report_id)}
                className="w-full bg-green-600 text-white py-1.5 rounded-lg text-sm hover:bg-green-700"
              >
                ⬇ Download .xlsx
              </button>
            </div>
          )}
          {report?.error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm">{report.error}</div>
          )}
        </div>

        {/* CSV Export */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">📄</span>
            <div>
              <h3 className="font-semibold text-gray-800">CSV Export</h3>
              <p className="text-xs text-gray-400">Raw data for further analysis</p>
            </div>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Export all comments with sentiment labels, confidence scores, and metadata as a CSV file.
          </p>
          <button
            onClick={downloadCsv}
            disabled={csvLoading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium text-sm"
          >
            {csvLoading ? 'Preparing...' : '⬇ Download CSV'}
          </button>
        </div>

        {/* Info card */}
        <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 border border-indigo-100 md:col-span-2">
          <h3 className="font-semibold text-indigo-800 mb-3 text-sm">What's included in reports</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-indigo-700">
            {['All comment text', 'Sentiment labels', 'Confidence scores', 'Source & date', 'Language info', 'Sentiment summary', 'Analysis metadata', 'Export timestamp'].map(item => (
              <div key={item} className="flex items-center gap-1.5">
                <span className="text-green-500">✓</span> {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
