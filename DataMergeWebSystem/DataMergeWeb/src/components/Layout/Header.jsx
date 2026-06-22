import { Bell } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const PAGE_TITLES = {
  '/home': 'Trang chủ',
  '/people-merge': 'Dọn dẹp & Gộp Hồ Sơ',
  '/info-append': 'Bổ sung thông tin',
  '/goods-merge': 'Gộp Hàng Hóa',
};

export default function Header() {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] || 'DataMerge';

  return (
    <header className="h-16 bg-white flex items-center justify-between px-8 flex-shrink-0"
      style={{ borderBottom: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
      <div>
        <h1 className="text-lg font-semibold text-gray-800 leading-none">{title}</h1>
        <div className="text-xs text-gray-400 mt-0.5">DataMerge Web System</div>
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
