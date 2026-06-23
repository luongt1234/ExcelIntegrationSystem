import { Bell, Users, FileStack, Package, Home } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const PAGE_TITLES = {
  '/home': { title: 'Trang chủ', icon: Home },
  '/people-merge': { title: 'Dọn dẹp & Gộp Hồ Sơ', icon: Users },
  '/info-append': { title: 'Bổ sung thông tin', icon: FileStack },
  '/goods-merge': { title: 'Gộp Hàng Hóa', icon: Package },
};

export default function Header() {
  const { pathname } = useLocation();
  const pageInfo = PAGE_TITLES[pathname] || { title: 'DataMerge', icon: null };
  const IconComponent = pageInfo.icon;

  return (
    <header className="h-16 bg-white flex items-center justify-between px-8 flex-shrink-0"
      style={{ borderBottom: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
      <div className="flex items-center space-x-3">
        {IconComponent && (
          <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center">
            <IconComponent size={18} />
          </div>
        )}
        <div>
          <h1 className="text-lg font-semibold text-gray-800 leading-none">{pageInfo.title}</h1>
          <div className="text-xs text-gray-400 mt-0.5">DataMerge Web System</div>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <button className="relative w-9 h-9 rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
          <Bell size={16} />
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-600 border-2 border-white text-white text-[9px] font-bold flex items-center justify-center">3</span>
        </button>
        <div className="h-8 w-px bg-gray-200" />
        <div className="text-xs text-gray-500">v1.0.0</div>
      </div>
    </header>
  );
}
