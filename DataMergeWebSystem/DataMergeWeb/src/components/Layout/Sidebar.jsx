import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Home, Users, Layers, Package, LogOut, ChevronRight, Menu } from 'lucide-react';

const menus = [
  { name: 'Trang chủ', path: '/home', icon: Home },
  { name: 'Gộp Hồ Sơ', path: '/people-merge', icon: Users },
  { name: 'Bổ sung thông tin', path: '/info-append', icon: Layers },
  { name: 'Gộp Hàng Hóa', path: '/goods-merge', icon: Package },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <aside className={`flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out relative ${isCollapsed ? 'w-20' : 'w-64'}`}
      style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)', borderRight: '1px solid rgba(255,255,255,0.05)' }}>

      {/* Toggle Button */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-6 w-6 h-6 bg-slate-800 text-slate-300 rounded-full flex items-center justify-center border border-slate-600 hover:bg-slate-700 hover:text-white transition-colors z-50 cursor-pointer shadow-md"
        title={isCollapsed ? "Mở rộng" : "Thu gọn"}
      >
        <ChevronRight size={14} className={`transition-transform duration-300 ${isCollapsed ? '' : 'rotate-180'}`} />
      </button>

      {/* Logo */}
      <div className={`flex items-center px-6 py-5 ${isCollapsed ? 'justify-center px-0' : 'space-x-3'}`} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
          <Layers size={18} className="text-white" />
        </div>
        {!isCollapsed && (
          <div className="overflow-hidden transition-all duration-300 whitespace-nowrap">
            <div className="text-white font-bold text-sm leading-none">DataMerge</div>
            <div className="text-slate-400 text-xs mt-0.5">Web System</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto overflow-x-hidden">
        {!isCollapsed && <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider px-3 mb-3 whitespace-nowrap">Menu</div>}
        {menus.map(({ name, path, icon: Icon }) => (
          <NavLink key={path} to={path}
            className={({ isActive }) =>
              `group flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isCollapsed ? 'justify-center' : 'space-x-3'
              } ${
                isActive
                  ? 'text-white shadow-lg'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`
            }
            title={isCollapsed ? name : ""}
            style={({ isActive }) => isActive
              ? { background: 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(99,102,241,0.2))', border: '1px solid rgba(99,102,241,0.3)' }
              : {}
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={isCollapsed ? 20 : 18} className={`flex-shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                {!isCollapsed && <span className="flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{name}</span>}
                {!isCollapsed && isActive && <ChevronRight size={14} className="text-blue-400 flex-shrink-0" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User info + Logout */}
      <div className="p-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className={`flex items-center rounded-xl ${isCollapsed ? 'justify-center py-3' : 'space-x-3 px-3 py-3'}`} style={{ background: 'rgba(255,255,255,0.04)' }}>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
            title={isCollapsed ? user.username || 'User' : ""}
          >
            {(user.username || 'U')[0].toUpperCase()}
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">{user.username || 'User'}</div>
              <div className="text-slate-500 text-xs truncate">{user.role || 'Admin'}</div>
            </div>
          )}
          <button onClick={handleLogout} title="Đăng xuất"
            className={`p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-colors flex-shrink-0 ${isCollapsed ? 'hidden' : ''}`}>
            <LogOut size={15} />
          </button>
        </div>
        {/* If collapsed, maybe show logout below avatar? For now just hide it or keep it simple. */}
        {isCollapsed && (
          <button onClick={handleLogout} title="Đăng xuất"
            className="w-full mt-2 flex justify-center p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-colors">
            <LogOut size={18} />
          </button>
        )}
      </div>
    </aside>
  );
}
