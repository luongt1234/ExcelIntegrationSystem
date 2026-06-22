import { NavLink, useNavigate } from 'react-router-dom';
import { Home, Users, Layers, Package, LogOut, ChevronRight } from 'lucide-react';

const menus = [
  { name: 'Trang chủ', path: '/home', icon: Home },
  { name: 'Gộp Hồ Sơ', path: '/people-merge', icon: Users },
  { name: 'Bổ sung thông tin', path: '/info-append', icon: Layers },
  { name: 'Gộp Hàng Hóa', path: '/goods-merge', icon: Package },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-full"
      style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)', borderRight: '1px solid rgba(255,255,255,0.05)' }}>

      {/* Logo */}
      <div className="flex items-center space-x-3 px-6 py-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
          <Layers size={18} className="text-white" />
        </div>
        <div>
          <div className="text-white font-bold text-sm leading-none">DataMerge</div>
          <div className="text-slate-400 text-xs mt-0.5">Web System</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider px-3 mb-3">Menu</div>
        {menus.map(({ name, path, icon: Icon }) => (
          <NavLink key={path} to={path}
            className={({ isActive }) =>
              `group flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'text-white shadow-lg'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`
            }
            style={({ isActive }) => isActive
              ? { background: 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(99,102,241,0.2))', border: '1px solid rgba(99,102,241,0.3)' }
              : {}
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={18} className={isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'} />
                <span className="flex-1">{name}</span>
                {isActive && <ChevronRight size={14} className="text-blue-400" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User info + Logout */}
      <div className="p-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center space-x-3 px-3 py-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
            {(user.username || 'U')[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-white text-sm font-medium truncate">{user.username || 'User'}</div>
            <div className="text-slate-500 text-xs">{user.role || 'Admin'}</div>
          </div>
          <button onClick={handleLogout} title="Đăng xuất"
            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-colors flex-shrink-0">
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
