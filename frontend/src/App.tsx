/**
 * Knowledge Keeper - 主应用组件
 */

import React, { useEffect } from 'react';
import { useAppStore } from './stores';
import Sidebar from './components/Sidebar';
import { MobileHeader, MobileBottomNav, MobileOverlay } from './components/MobileNav';
import Notification from './components/Notification';
import Home from './pages/Home';
import Bookmarks from './pages/Bookmarks';
import Chat from './pages/Chat';
import Search from './pages/Search';
import Settings from './pages/Settings';
import { hasLocalWechat, hasLocalCreate } from './localModules';
// 直接导入本地公众号模块（如果存在）
import Wechat from './local/Wechat';
// 直接导入创作模块（如果存在）
import { Create } from './local/Create';
import './App.css';

// 基础页面映射
const basePages: Record<string, React.FC> = {
  home: Home,
  bookmarks: Bookmarks,
  chat: Chat,
  search: Search,
  settings: Settings,
};

// 合并页面映射（包含本地模块）
const pages: Record<string, React.FC> = {
  ...basePages,
  ...(hasLocalWechat ? { wechat: Wechat } : {}),
  ...(hasLocalCreate ? { create: Create } : {}),
};

function App() {
  const { currentView, sidebarOpen, setSidebarOpen } = useAppStore();

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && savedTheme !== 'system') {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  // 监听窗口大小变化，移动端自动关闭侧边栏
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 768 && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen, setSidebarOpen]);

  // 获取当前页面组件
  const CurrentPage = pages[currentView] || Home;

  return (
    <div className="app">
      {/* 移动端顶部头部 */}
      <MobileHeader />

      {/* 移动端遮罩层 */}
      <MobileOverlay />

      {/* 侧边栏 */}
      <Sidebar />

      {/* 主内容区 */}
      <main className={`app__main ${sidebarOpen ? 'app__main--sidebar-open' : 'app__main--sidebar-closed'}`}>
        <CurrentPage />
      </main>

      {/* 移动端底部导航 */}
      <MobileBottomNav />

      {/* 全局通知 */}
      <Notification />
    </div>
  );
}

export default App;

