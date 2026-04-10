import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/analyze', label: 'Analyze', icon: '🔍' },
  { to: '/summarize', label: 'Summarize', icon: '✨' },
  { to: '/upload', label: 'Upload', icon: '📤' },
  { to: '/comments', label: 'Comments', icon: '💬' },
  { to: '/reports', label: 'Reports', icon: '📋' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/') }

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-56 bg-white border-r flex flex-col">
        <div className="p-5 border-b">
          <h1 className="font-bold text-gray-800 text-sm leading-tight">MCA21 Sentiment<br/>Analysis</h1>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(n => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}>
              <span>{n.icon}</span>{n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t">
          <p className="text-xs text-gray-500 mb-1 truncate">{user?.email}</p>
          <p className="text-xs text-gray-400 capitalize mb-3">{user?.role}</p>
          <button onClick={handleLogout} className="w-full text-xs text-red-500 hover:text-red-700 text-left">Sign out</button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
