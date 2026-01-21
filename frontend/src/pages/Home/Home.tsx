/**
 * 首页组件
 */

import React, { useEffect, useState } from 'react';
import {
    Bookmark,
    Tag,
    MessageSquare,
    TrendingUp,
    Plus,
    ArrowRight,
    Sparkles,
    Database,
    Link,
    FileText,
    ExternalLink,
} from 'lucide-react';
import { searchApi, bookmarkApi } from '../../services/api';
import type { SearchStats, Bookmark as BookmarkType } from '../../services/api';
import { useAppStore } from '../../stores';
import './Home.css';

const Home: React.FC = () => {
    const { setCurrentView } = useAppStore();
    const [stats, setStats] = useState<SearchStats | null>(null);
    const [recentBookmarks, setRecentBookmarks] = useState<BookmarkType[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsData, bookmarksData] = await Promise.all([
                searchApi.stats(),
                bookmarkApi.list({ page_size: 5 }),
            ]);
            setStats(statsData);
            setRecentBookmarks(bookmarksData.items);
        } catch (error) {
            console.error('加载数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const quickActions = [
        {
            id: 'add-url',
            label: '添加网页',
            description: '保存网页内容到知识库',
            icon: Plus,
            color: 'var(--color-primary)',
            action: () => setCurrentView('bookmarks'),
        },
        {
            id: 'chat',
            label: '开始对话',
            description: '向知识库提问',
            icon: MessageSquare,
            color: 'var(--color-accent)',
            action: () => setCurrentView('chat'),
        },
        {
            id: 'search',
            label: '搜索知识',
            description: '在知识库中搜索',
            icon: TrendingUp,
            color: 'var(--color-accent-green)',
            action: () => setCurrentView('search'),
        },
    ];

    return (
        <div className="home">
            {/* 欢迎区域 */}
            <section className="home__hero">
                <div className="home__hero-content">
                    <div className="home__hero-badge">
                        <Sparkles size={16} />
                        <span>AI 驱动</span>
                    </div>
                    <h1 className="home__hero-title">
                        欢迎使用 <span className="gradient-text">Knowledge Keeper</span>
                    </h1>
                    <p className="home__hero-subtitle">
                        智能收集、整理、学习 - 让 AI 帮你管理知识
                    </p>
                </div>

                {/* 快捷操作 */}
                <div className="home__quick-actions">
                    {quickActions.map((action) => (
                        <button
                            key={action.id}
                            className="home__action-card"
                            onClick={action.action}
                        >
                            <div
                                className="home__action-icon"
                                style={{ background: `${action.color}20`, color: action.color }}
                            >
                                <action.icon size={24} />
                            </div>
                            <div className="home__action-content">
                                <span className="home__action-label">{action.label}</span>
                                <span className="home__action-desc">{action.description}</span>
                            </div>
                            <ArrowRight size={18} className="home__action-arrow" />
                        </button>
                    ))}
                </div>
            </section>

            {/* 统计卡片 */}
            <section className="home__stats">
                <h2 className="home__section-title">知识库概览</h2>
                <div className="home__stats-grid">
                    <div className="home__stat-card">
                        <div className="home__stat-icon" style={{ background: 'rgba(99, 102, 241, 0.2)' }}>
                            <Bookmark size={24} style={{ color: 'var(--color-primary)' }} />
                        </div>
                        <div className="home__stat-content">
                            <span className="home__stat-value">
                                {loading ? '-' : stats?.total_bookmarks || 0}
                            </span>
                            <span className="home__stat-label">收藏总数</span>
                        </div>
                    </div>

                    <div className="home__stat-card">
                        <div className="home__stat-icon" style={{ background: 'rgba(34, 211, 238, 0.2)' }}>
                            <Tag size={24} style={{ color: 'var(--color-accent)' }} />
                        </div>
                        <div className="home__stat-content">
                            <span className="home__stat-value">
                                {loading ? '-' : stats?.total_tags || 0}
                            </span>
                            <span className="home__stat-label">标签数量</span>
                        </div>
                    </div>

                    <div className="home__stat-card">
                        <div className="home__stat-icon" style={{ background: 'rgba(52, 211, 153, 0.2)' }}>
                            <Database size={24} style={{ color: 'var(--color-accent-green)' }} />
                        </div>
                        <div className="home__stat-content">
                            <span className="home__stat-value">
                                {loading ? '-' : stats?.embedded_count || 0}
                            </span>
                            <span className="home__stat-label">已向量化</span>
                        </div>
                    </div>
                </div>

                {/* 类型分布 */}
                {stats && stats.by_type && (
                    <div className="home__type-stats">
                        <div className="home__type-item">
                            <span className="home__type-label">网页</span>
                            <div className="home__type-bar">
                                <div
                                    className="home__type-fill"
                                    style={{
                                        width: `${(stats.by_type.url / Math.max(stats.total_bookmarks, 1)) * 100}%`,
                                        background: 'var(--color-primary)',
                                    }}
                                />
                            </div>
                            <span className="home__type-count">{stats.by_type.url || 0}</span>
                        </div>
                        <div className="home__type-item">
                            <span className="home__type-label">笔记</span>
                            <div className="home__type-bar">
                                <div
                                    className="home__type-fill"
                                    style={{
                                        width: `${(stats.by_type.note / Math.max(stats.total_bookmarks, 1)) * 100}%`,
                                        background: 'var(--color-accent)',
                                    }}
                                />
                            </div>
                            <span className="home__type-count">{stats.by_type.note || 0}</span>
                        </div>
                        <div className="home__type-item">
                            <span className="home__type-label">文件</span>
                            <div className="home__type-bar">
                                <div
                                    className="home__type-fill"
                                    style={{
                                        width: `${(stats.by_type.file / Math.max(stats.total_bookmarks, 1)) * 100}%`,
                                        background: 'var(--color-accent-green)',
                                    }}
                                />
                            </div>
                            <span className="home__type-count">{stats.by_type.file || 0}</span>
                        </div>
                    </div>
                )}
            </section>

            {/* 知识库内容预览 */}
            {recentBookmarks.length > 0 && (
                <section className="home__recent">
                    <div className="home__section-header">
                        <h2 className="home__section-title">知识库内容</h2>
                        <button
                            className="home__view-all"
                            onClick={() => setCurrentView('bookmarks')}
                        >
                            查看全部 <ArrowRight size={16} />
                        </button>
                    </div>
                    <div className="home__recent-list">
                        {recentBookmarks.map((bookmark) => (
                            <div key={bookmark.id} className="home__recent-item">
                                <div className="home__recent-icon">
                                    {bookmark.type === 'url' ? <Link size={16} /> : <FileText size={16} />}
                                </div>
                                <div className="home__recent-content">
                                    <span className="home__recent-title">{bookmark.title}</span>
                                    {bookmark.summary && (
                                        <span className="home__recent-summary">{bookmark.summary}</span>
                                    )}
                                    {bookmark.url && (
                                        <a
                                            href={bookmark.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="home__recent-url"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            {new URL(bookmark.url).hostname}
                                            <ExternalLink size={10} />
                                        </a>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* 空状态提示 */}
            {stats && stats.total_bookmarks === 0 && (
                <section className="home__empty">
                    <div className="home__empty-icon">
                        <Sparkles size={48} />
                    </div>
                    <h3>开始构建你的知识库</h3>
                    <p>添加网页链接、笔记或文件，AI 会自动帮你整理和总结</p>
                    <button
                        className="btn btn-primary"
                        onClick={() => setCurrentView('bookmarks')}
                    >
                        <Plus size={18} />
                        添加第一个收藏
                    </button>
                </section>
            )}
        </div>
    );
};

export default Home;

