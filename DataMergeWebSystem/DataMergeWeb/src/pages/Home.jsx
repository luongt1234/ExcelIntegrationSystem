import { Link } from 'react-router-dom';
import { Users, Layers, Package, ArrowUpRight, TrendingUp, FileText, CheckCircle } from 'lucide-react';

const features = [
  {
    title: 'Dọn dẹp & Gộp Hồ Sơ',
    description: 'Gộp nhiều file Excel, tự động loại trùng theo khóa chung và chuẩn hóa dữ liệu.',
    icon: Users,
    path: '/people-merge',
    gradient: 'from-blue-500 to-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-100',
    tag: 'Smart Merge',
  },
  {
    title: 'Bổ sung thông tin',
    description: 'Kéo thả (Drag & Drop) ghép nối cột từ file phụ vào file gốc — Left Join trực quan.',
    icon: Layers,
    path: '/info-append',
    gradient: 'from-indigo-500 to-purple-600',
    bg: 'bg-indigo-50',
    border: 'border-indigo-100',
    tag: 'Left Join',
  },
  {
    title: 'Gộp Hàng Hóa',
    description: 'So khớp Input với Catalog theo Similarity Score, phân loại 3 nhóm và xuất kết quả.',
    icon: Package,
    path: '/goods-merge',
    gradient: 'from-purple-500 to-pink-600',
    bg: 'bg-purple-50',
    border: 'border-purple-100',
    tag: 'Catalog Matcher',
  },
];

const stats = [
  { label: 'Chức năng', value: '3', icon: CheckCircle, color: 'text-blue-600', bg: 'bg-blue-50' },
  { label: 'Định dạng hỗ trợ', value: '.xlsx / .xls', icon: FileText, color: 'text-indigo-600', bg: 'bg-indigo-50' },
  { label: 'Giới hạn file', value: '100 MB', icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
];

export default function Home() {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in-up">
      {/* Hero Banner */}
      <div className="rounded-2xl overflow-hidden relative"
        style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #1e40af 60%, #3730a3 100%)' }}>
        <div className="absolute inset-0 opacity-5"
          style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 50%, white 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
        <div className="relative z-10 px-10 py-10 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Chào mừng trở lại! 👋</h1>
            <p className="text-blue-200 text-lg max-w-lg">
              Chọn công cụ bên dưới để bắt đầu xử lý và tích hợp dữ liệu Excel của bạn.
            </p>
          </div>
          <div className="hidden xl:flex items-center space-x-4">
            <div className="text-right text-white/70 text-sm">Tài khoản</div>
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-white font-bold text-lg"
              style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.2)' }}>
              A
            </div>
          </div>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg }, i) => (
          <div key={i} className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className={`w-11 h-11 rounded-xl ${bg} flex items-center justify-center flex-shrink-0`}>
              <Icon size={20} className={color} />
            </div>
            <div>
              <div className="text-xl font-bold text-gray-800">{value}</div>
              <div className="text-xs text-gray-500 mt-0.5">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Feature Cards */}
      <div>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">🛠 Công cụ xử lý dữ liệu</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map(({ title, description, icon: Icon, path, gradient, bg, border, tag }) => (
            <Link key={path} to={path}
              className={`group flex flex-col bg-white rounded-2xl shadow-sm border ${border} overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300`}>
              {/* Card top strip */}
              <div className={`h-1.5 w-full bg-gradient-to-r ${gradient}`} />
              <div className="p-6 flex flex-col flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                    <Icon size={24} className={`bg-gradient-to-br ${gradient} bg-clip-text`} style={{ color: 'transparent', backgroundClip: 'text', WebkitBackgroundClip: 'text' }} />
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-500">{tag}</span>
                </div>
                <h3 className="text-base font-bold text-gray-800 mb-2">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed flex-1">{description}</p>
                <div className={`mt-5 flex items-center text-sm font-semibold bg-gradient-to-r ${gradient} bg-clip-text`}
                  style={{ color: 'transparent', backgroundClip: 'text', WebkitBackgroundClip: 'text' }}>
                  <span>Bắt đầu ngay</span>
                  <ArrowUpRight size={15} className="ml-1 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" style={{ color: 'inherit' }} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
