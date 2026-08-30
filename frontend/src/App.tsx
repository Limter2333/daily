import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import BriefingView from './components/briefingView';
import Settings from './components/Settings';
import { healthCheck } from './services/api';

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        isActive
          ? 'bg-white/20 text-white'
          : 'text-white/80 hover:bg-white/10 hover:text-white'
      }`}
    >
      {children}
    </Link>
  );
}

function App() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthCheck();
        setIsHealthy(true);
      } catch {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* 顶部导航栏 */}
        <header className="gradient-bg shadow-lg">
          <div className="container-responsive">
            <div className="flex items-center justify-between h-16">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <span className="text-2xl">📰</span>
                <h1 className="text-xl font-bold text-white">每日早报晚报</h1>
              </div>

              {/* 导航链接 */}
              <nav className="flex items-center space-x-2">
                <NavLink to="/">首页</NavLink>
                <NavLink to="/briefings">早报晚报</NavLink>
                <NavLink to="/settings">设置</NavLink>
              </nav>

              {/* 状态指示器 */}
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isHealthy === null
                      ? 'bg-yellow-400'
                      : isHealthy
                      ? 'bg-green-400'
                      : 'bg-red-400'
                  }`}
                />
                <span className="text-xs text-white/80">
                  {isHealthy === null
                    ? '检查中...'
                    : isHealthy
                    ? '服务正常'
                    : '服务异常'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* 主内容区 */}
        <main className="py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/briefings" element={<BriefingView />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        {/* 底部 */}
        <footer className="bg-white border-t border-gray-200 py-4 mt-8">
          <div className="container-responsive text-center text-sm text-gray-500">
            <p>每日早报晚报系统 v1.0.0</p>
            <p className="mt-1">自动获取财经、科技、半导体、AI等新闻</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
