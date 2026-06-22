import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Lock, User, Eye, EyeOff } from 'lucide-react';
import api from '../services/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.post('/api/auth/login', { username, password });
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/home');
    } catch (err) {
      setError(err.response?.data?.message || 'Tài khoản hoặc mật khẩu không đúng.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex">
      {/* Left Panel – Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #1e40af 50%, #3730a3 100%)' }}>
        {/* Background circles */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #60a5fa, transparent)' }} />
        <div className="absolute -bottom-32 -right-16 w-80 h-80 rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, #a78bfa, transparent)' }} />
        <div className="absolute top-1/3 right-8 w-40 h-40 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, #34d399, transparent)' }} />

        <div className="relative z-10 flex flex-col items-start justify-center px-16 text-white">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-8 shadow-lg"
            style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)' }}>
            <Layers size={32} className="text-white" />
          </div>
          <h1 className="text-4xl font-bold mb-4 leading-tight">
            DataMerge<br /><span className="text-blue-300">Web</span>
          </h1>
          <p className="text-blue-100 text-lg mb-8 max-w-sm leading-relaxed">
            Hệ thống tích hợp & chuẩn hóa dữ liệu Excel thông minh, hiệu quả cao.
          </p>
          <div className="space-y-4">
            {[
              { emoji: '⚡', text: 'Gộp & Dedup hàng nghìn dòng chỉ trong vài giây' },
              { emoji: '🔗', text: 'Left Join đa file với giao diện kéo-thả trực quan' },
              { emoji: '🎯', text: 'So khớp Hàng hóa bằng AI Similarity' },
            ].map((item, i) => (
              <div key={i} className="flex items-start space-x-3">
                <span className="text-xl mt-0.5">{item.emoji}</span>
                <span className="text-blue-100 text-sm">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel – Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md animate-fade-in-up">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center space-x-3 mb-10">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
              <Layers size={22} className="text-white" />
            </div>
            <span className="text-xl font-bold text-gray-800">DataMerge Web</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Đăng nhập</h2>
            <p className="text-gray-500">Nhập thông tin tài khoản để tiếp tục</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start space-x-3">
              <span className="text-red-500 mt-0.5 text-lg">⚠️</span>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Tên đăng nhập</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User size={18} className="text-gray-400" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-gray-900 text-sm placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 shadow-sm"
                  placeholder="Nhập tên đăng nhập..."
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Mật khẩu</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-gray-400" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-12 py-3.5 bg-white border border-gray-200 rounded-xl text-gray-900 text-sm placeholder-gray-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 shadow-sm"
                  placeholder="Nhập mật khẩu..."
                  required
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl font-semibold text-white text-sm shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
              style={{ background: loading ? '#93c5fd' : 'linear-gradient(135deg, #2563eb, #1d4ed8)' }}
            >
              {loading ? (
                <span className="flex items-center justify-center space-x-2">
                  <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Đang xử lý...</span>
                </span>
              ) : 'Đăng nhập →'}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-gray-400">
            Tài khoản mặc định: <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">admin</span> /&nbsp;
            <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">admin</span>
          </p>
        </div>
      </div>
    </div>
  );
}
