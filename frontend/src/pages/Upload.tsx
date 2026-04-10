import { useState } from 'react'
import api from '../api'

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState('')
  const [manual, setManual] = useState('')
  const [source, setSource] = useState('public_consultation')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'file' | 'manual'>('manual')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null
    setFile(f)
    setFileName(f ? f.name : '')
    setResult(null)
  }

  const uploadFile = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const ext = file.name.split('.').pop()?.toLowerCase()
      const endpoint = ext === 'csv' ? '/upload/csv' : '/upload/excel'
      const { data } = await api.post(endpoint, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(data)
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Upload failed'
      setResult({ error: typeof msg === 'string' ? msg : JSON.stringify(msg) })
    }
    setLoading(false)
  }

  const submitManual = async () => {
    if (!manual.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await api.post('/upload/manual', { comment_text: manual, source })
      setResult({ success: true, stored_count: 1, total_comments: 1 })
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Failed'
      setResult({ error: typeof msg === 'string' ? msg : JSON.stringify(msg) })
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Comments</h2>
      <div className="bg-white rounded-xl p-6 shadow-sm border mb-6">
        <div className="flex gap-2 mb-6">
          {(['manual', 'file'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${tab === t ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{t === 'file' ? 'CSV / Excel' : 'Manual Entry'}</button>
          ))}
        </div>

        {tab === 'manual' && (
          <div className="space-y-4">
            <textarea className="w-full border rounded-lg p-3 h-28 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" placeholder="Enter comment text..." value={manual} onChange={e => setManual(e.target.value)} />
            <input className="w-full border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Source (e.g. public_consultation)" value={source} onChange={e => setSource(e.target.value)} />
            <button onClick={submitManual} disabled={loading || !manual.trim()} className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
              {loading ? 'Submitting...' : 'Submit Comment'}
            </button>
          </div>
        )}

        {tab === 'file' && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <p className="text-gray-500 mb-3 text-sm">Upload CSV or Excel file with a <code className="bg-gray-100 px-1 rounded">comment_text</code> column</p>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} className="text-sm" />
              {fileName && <p className="mt-2 text-sm text-blue-600 font-medium">Selected: {fileName}</p>}
            </div>
            <button
              onClick={uploadFile}
              disabled={loading || !file}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Uploading...' : `Upload File${file ? ` (${file.name})` : ''}`}
            </button>
          </div>
        )}
      </div>

      {result && (
        <div className={`rounded-xl p-4 text-sm ${result.error ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
          {result.error ? result.error : (
            <div>
              <p className="font-semibold">Success!</p>
              {result.stored_count !== undefined && <p>Stored {result.stored_count} of {result.total_comments} comments</p>}
              {result.validation_errors?.length > 0 && <p>{result.validation_errors.length} validation errors</p>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
