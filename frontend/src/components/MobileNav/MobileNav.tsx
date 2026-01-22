/**
 * 移动端导航组件
 * 包含底部 Tab 导航和顶部汉堡菜单
 */

import React from 'react';
import {
    Home,
    Bookmark,
    MessageSquare,
    Search,
    Settings,
    Menu,
    X,
} from 'lucide-react';
import { useAppStore } from '../../stores';
import './MobileNav.css';

// 底部导航项
const bottomNavItems = [
    { id: 'home', label: '首页', icon: Home },
    { id: 'bookmarks', label: '收藏', icon: Bookmark },
    { id: 'chat', label: '问答', icon: MessageSquare },
    { id: 'search', label: '搜索', icon: Search },
    { id: 'settings', label: '设置', icon: Settings },
] as const;

// 移动端顶部头部
export const MobileHeader: React.FC = () => {
    const { sidebarOpen, toggleSidebar, currentView } = useAppStore();

    // 获取当前页面标题
    const getPageTitle = () => {
        switch (currentView) {
            case 'home': return '首页';
            case 'bookmarks': return '我的收藏';
            case 'chat': return '智能问答';
            case 'search': return '搜索';
            case 'settings': return '设置';
            default: return 'Knowledge Keeper';
        }
    };

    return (
        <header className="mobile-header">
            <button
                className="mobile-header__menu-btn"
                onClick={toggleSidebar}
                aria-label={sidebarOpen ? '关闭菜单' : '打开菜单'}
            >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <h1 className="mobile-header__title">{getPageTitle()}</h1>
            <div className="mobile-header__spacer" />
        </header>
    );
};

// 移动端底部导航
export const MobileBottomNav: React.FC = () => {
    const { currentView, setCurrentView } = useAppStore();

    return (
        <nav className="mobile-bottom-nav">
            {bottomNavItems.map((item) => (
                <button
                    key={item.id}
                    className={`mobile-bottom-nav__item ${currentView === item.id ? 'mobile-bottom-nav__item--active' : ''}`}
                    onClick={() => setCurrentView(item.id as any)}
                >
                    <item.icon size={20} />
                    <span>{item.label}</span>
                </button>
            ))}
        </nav>
    );
};

// 移动端遮罩层（侧边栏打开时）
export const MobileOverlay: React.FC = () => {
    const { sidebarOpen, toggleSidebar } = useAppStore();

    if (!sidebarOpen) return null;

    return (
        <div
            className="mobile-overlay"
            onClick={toggleSidebar}
            aria-label="关闭菜单"
        />
    );
};
