import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Dashboard', path: '/', icon: '▪' },
  { label: 'Analyse', path: '/analyse', icon: '▪' },
  { label: 'Incidents', path: '/incidents', icon: '▪' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <img src="/autosoc_favicon.svg" alt="AutoSOC" className="brand-icon" />
        <span className="brand-name">AUTO<span>SOC</span></span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item--active' : ''}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="status-dot status-dot--online" />
        <span>System operational</span>
      </div>
    </aside>
  )
}