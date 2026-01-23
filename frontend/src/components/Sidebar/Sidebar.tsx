/**
 * 侧边栏组件
 */

import React from 'react';
import {
    Home,
    Bookmark,
    MessageSquare,
    Search,
    Settings,
    ChevronLeft,
    ChevronRight,
    Sparkles,
    QrCode,
} from 'lucide-react';
import { useAppStore } from '../../stores';
import { hasLocalWechat } from '../../localModules';
import './Sidebar.css';

// 基础导航菜单项
const baseNavItems = [
    { id: 'home', label: '首页', icon: Home },
    { id: 'bookmarks', label: '收藏', icon: Bookmark },
    { id: 'chat', label: '智能问答', icon: MessageSquare },
    { id: 'search', label: '搜索', icon: Search },
    { id: 'settings', label: '设置', icon: Settings },
] as const;

// 本地模块导航项（仅在本地模块存在时添加）
const localNavItems = hasLocalWechat ? [
    { id: 'wechat', label: '公众号', icon: QrCode },
] : [];

// 合并导航项
const navItems = [...baseNavItems, ...localNavItems];

const Sidebar: React.FC = () => {
    const { sidebarOpen, toggleSidebar, currentView, setCurrentView } = useAppStore();

    return (
        <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : 'sidebar--closed'}`}>
            {/* Logo */}
            <div className="sidebar__logo">
                <div className="sidebar__logo-icon">
                    <Sparkles size={24} />
                </div>
                {sidebarOpen && (
                    <span className="sidebar__logo-text">Knowledge Keeper</span>
                )}
            </div>

            {/* 导航菜单 */}
            <nav className="sidebar__nav">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        className={`sidebar__nav-item ${currentView === item.id ? 'sidebar__nav-item--active' : ''}`}
                        onClick={() => setCurrentView(item.id as any)}
                        title={item.label}
                    >
                        <item.icon size={20} />
                        {sidebarOpen && <span>{item.label}</span>}
                    </button>
                ))}
            </nav>

            {/* 本地模块分隔线（仅当有本地模块时显示） */}
            {hasLocalWechat && sidebarOpen && (
                <div className="sidebar__local-badge">
                    <span>本地功能</span>
                </div>
            )}

            {/* 折叠按钮 */}
            <button className="sidebar__toggle" onClick={toggleSidebar}>
                {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
            </button>
        </aside>
    );
};

export default Sidebar;
