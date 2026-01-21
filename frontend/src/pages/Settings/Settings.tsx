/**
 * 设置页面组件
 */

import React, { useState, useEffect } from 'react';
import {
    Settings as SettingsIcon,
    Cpu,
    Database,
    Palette,
    Info,
    ExternalLink,
    Github,
    Sun,
    Moon,
    Monitor,
} from 'lucide-react';
import './Settings.css';

type ThemeMode = 'system' | 'light' | 'dark';

const Settings: React.FC = () => {
    const [theme, setTheme] = useState<ThemeMode>(() => {
        return (localStorage.getItem('theme') as ThemeMode) || 'system';
    });

    // 应用主题
    useEffect(() => {
        const root = document.documentElement;

        if (theme === 'system') {
            root.removeAttribute('data-theme');
        } else {
            root.setAttribute('data-theme', theme);
        }

        localStorage.setItem('theme', theme);
    }, [theme]);

    const handleThemeChange = (newTheme: ThemeMode) => {
        setTheme(newTheme);
    };

    return (
        <div className="settings-page">
            <header className="settings-page__header">
                <SettingsIcon size={32} />
                <div>
                    <h1>设置</h1>
                    <p>管理应用配置</p>
                </div>
            </header>

            <div className="settings-page__content">
                {/* AI 模型配置 */}
                <section className="settings-section">
                    <div className="settings-section__header">
                        <Cpu size={20} />
                        <h2>AI 模型</h2>
                    </div>
                    <div className="settings-section__content">
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">当前模型</span>
                                <span className="settings-item__desc">用于生成摘要、标签和对话</span>
                            </div>
                            <div className="settings-item__value">
                                <span className="settings-badge settings-badge--primary">豆包 (Doubao)</span>
                            </div>
                        </div>
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">API 配置</span>
                                <span className="settings-item__desc">在后端 .env 文件中配置</span>
                            </div>
                            <a href="#" className="settings-link">
                                查看配置说明
                                <ExternalLink size={14} />
                            </a>
                        </div>
                    </div>
                </section>

                {/* 知识库配置 */}
                <section className="settings-section">
                    <div className="settings-section__header">
                        <Database size={20} />
                        <h2>知识库</h2>
                    </div>
                    <div className="settings-section__content">
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">向量数据库</span>
                                <span className="settings-item__desc">用于语义搜索</span>
                            </div>
                            <div className="settings-item__value">
                                <span className="settings-badge">向量存储</span>
                            </div>
                        </div>
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">嵌入模型</span>
                                <span className="settings-item__desc">文本向量化</span>
                            </div>
                            <div className="settings-item__value">
                                <span className="settings-badge">豆包 Embedding</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* 外观设置 */}
                <section className="settings-section">
                    <div className="settings-section__header">
                        <Palette size={20} />
                        <h2>外观</h2>
                    </div>
                    <div className="settings-section__content">
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">主题</span>
                                <span className="settings-item__desc">选择界面配色方案</span>
                            </div>
                        </div>
                        <div className="theme-selector">
                            <button
                                className={`theme-option ${theme === 'system' ? 'theme-option--active' : ''}`}
                                onClick={() => handleThemeChange('system')}
                            >
                                <Monitor size={20} />
                                <span>跟随系统</span>
                            </button>
                            <button
                                className={`theme-option ${theme === 'light' ? 'theme-option--active' : ''}`}
                                onClick={() => handleThemeChange('light')}
                            >
                                <Sun size={20} />
                                <span>亮色</span>
                            </button>
                            <button
                                className={`theme-option ${theme === 'dark' ? 'theme-option--active' : ''}`}
                                onClick={() => handleThemeChange('dark')}
                            >
                                <Moon size={20} />
                                <span>暗色</span>
                            </button>
                        </div>
                    </div>
                </section>

                {/* 关于 */}
                <section className="settings-section">
                    <div className="settings-section__header">
                        <Info size={20} />
                        <h2>关于</h2>
                    </div>
                    <div className="settings-section__content">
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">Knowledge Keeper</span>
                                <span className="settings-item__desc">AI 驱动的知识管理应用</span>
                            </div>
                            <div className="settings-item__value">
                                <span className="settings-version">v1.0.0</span>
                            </div>
                        </div>
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">技术栈</span>
                                <span className="settings-item__desc">React + FastAPI + 向量搜索</span>
                            </div>
                        </div>
                        <div className="settings-about">
                            <p>
                                这是一个 AI 辅助开发的面试 Demo 项目，展示了完整的全栈开发能力，
                                包括前端 React 应用、后端 FastAPI 服务、向量数据库集成和多模型 AI 支持。
                            </p>
                            <div className="settings-about__links">
                                <a href="#" className="settings-about__link">
                                    <Github size={18} />
                                    查看源码
                                </a>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default Settings;

