/**
 * Knowledge Keeper - 主应用组件
 */

import React, { useEffect } from 'react';
import { useAppStore } from './stores';
import Sidebar from './components/Sidebar';
import Notification from './components/Notification';
import Home from './pages/Home';
import Bookmarks from './pages/Bookmarks';
import Chat from './pages/Chat';
import Search from './pages/Search';
import Settings from './pages/Settings';
import './App.css';

// 页面映射
const pages: Record<string, React.FC> = {
  home: Home,
  bookmarks: Bookmarks,
  chat: Chat,
  search: Search,
  settings: Settings,
};

function App() {
  const { currentView, sidebarOpen } = useAppStore();

  // 初始化主题
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme && savedTheme !== 'system') {
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  // 获取当前页面组件
  const CurrentPage = pages[currentView] || Home;

  return (
    <div className="app">
      {/* 侧边栏 */}
      <Sidebar />

      {/* 主内容区 */}
      <main className={`app__main ${sidebarOpen ? 'app__main--sidebar-open' : 'app__main--sidebar-closed'}`}>
        <CurrentPage />
      </main>

      {/* 全局通知 */}
      <Notification />
    </div>
  );
}

export default App;
