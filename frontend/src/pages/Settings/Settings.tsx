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
    Eye,
    EyeOff,
    Check,
    Loader2,
} from 'lucide-react';
import { useAppStore } from '../../stores';
import { configApi } from '../../services/api';
import './Settings.css';

type ThemeMode = 'system' | 'light' | 'dark';

interface AIProvider {
    id: string;
    name: string;
    description: string;
}

const AI_PROVIDERS: AIProvider[] = [
    { id: 'doubao', name: '豆包', description: '字节跳动火山引擎' },
    { id: 'openai', name: 'OpenAI', description: 'GPT-4 / GPT-3.5' },
    { id: 'claude', name: 'Claude', description: 'Anthropic Claude' },
    { id: 'gemini', name: 'Gemini', description: 'Google AI' },
    { id: 'deepseek', name: 'Deepseek', description: 'Deepseek AI' },
];

const Settings: React.FC = () => {
    const { showNotification } = useAppStore();
    const [theme, setTheme] = useState<ThemeMode>(() => {
        return (localStorage.getItem('theme') as ThemeMode) || 'system';
    });

    // AI 配置状态
    const [selectedProvider, setSelectedProvider] = useState('doubao');
    const [apiKey, setApiKey] = useState('');
    const [showApiKey, setShowApiKey] = useState(false);
    const [saving, setSaving] = useState(false);
    const [configuredProviders, setConfiguredProviders] = useState<Record<string, boolean>>({});

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

    // 加载已保存的配置
    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const response = await configApi.get();
            setSelectedProvider(response.provider);
            setConfiguredProviders(response.configured_providers || {});
        } catch (error) {
            // 使用默认值
        }
    };

    const handleThemeChange = (newTheme: ThemeMode) => {
        setTheme(newTheme);
    };

    const handleSaveConfig = async () => {
        if (!apiKey.trim()) {
            showNotification('error', '请输入 API Key');
            return;
        }

        setSaving(true);
        try {
            // 调用后端 API 保存到 .env 文件
            const response = await configApi.update({
                provider: selectedProvider,
                api_key: apiKey
            });

            setConfiguredProviders(response.configured_providers || {});
            setApiKey(''); // 清空输入框
            showNotification('success', response.message);
        } catch (error: any) {
            showNotification('error', error?.response?.data?.message || '保存失败');
        } finally {
            setSaving(false);
        }
    };

    // 当前选中的提供商是否已配置
    const isCurrentProviderConfigured = configuredProviders[selectedProvider] || false;

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
                        {/* 模型选择 */}
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">AI 服务提供商</span>
                                <span className="settings-item__desc">选择用于生成摘要、标签和对话的模型</span>
                            </div>
                        </div>
                        <div className="provider-selector">
                            {AI_PROVIDERS.map((provider) => (
                                <button
                                    key={provider.id}
                                    className={`provider-option ${selectedProvider === provider.id ? 'provider-option--active' : ''}`}
                                    onClick={() => setSelectedProvider(provider.id)}
                                >
                                    <span className="provider-option__name">{provider.name}</span>
                                    <span className="provider-option__desc">{provider.description}</span>
                                </button>
                            ))}
                        </div>

                        {/* API Key 输入 */}
                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__label">
                                    API 密钥
                                    {isCurrentProviderConfigured && (
                                        <span className="settings-badge settings-badge--success" style={{ marginLeft: '8px' }}>
                                            ✓ 已配置
                                        </span>
                                    )}
                                </span>
                                <span className="settings-item__desc">
                                    输入 {AI_PROVIDERS.find(p => p.id === selectedProvider)?.name} 的 API Key
                                </span>
                            </div>
                        </div>
                        <div className="api-key-input">
                            <div className="api-key-input__field">
                                <input
                                    type={showApiKey ? 'text' : 'password'}
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder={isCurrentProviderConfigured ? "输入新的 API Key 可覆盖..." : "请输入 API Key..."}
                                />
                                <button
                                    type="button"
                                    className="api-key-input__toggle"
                                    onClick={() => setShowApiKey(!showApiKey)}
                                >
                                    {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            <button
                                className="btn btn-primary"
                                onClick={handleSaveConfig}
                                disabled={saving}
                            >
                                {saving ? (
                                    <>
                                        <Loader2 size={16} className="animate-spin" />
                                        保存中...
                                    </>
                                ) : (
                                    <>
                                        <Check size={16} />
                                        保存配置
                                    </>
                                )}
                            </button>
                        </div>

                        <div className="settings-item">
                            <div className="settings-item__info">
                                <span className="settings-item__desc" style={{ color: 'var(--color-text-muted)' }}>
                                    💡 提示：配置会保存到后端 .env 文件，保存后需重启后端服务生效
                                </span>
                            </div>
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
                                <Monitor size={16} />
                                <span>跟随系统</span>
                            </button>
                            <button
                                className={`theme-option ${theme === 'light' ? 'theme-option--active' : ''}`}
                                onClick={() => handleThemeChange('light')}
                            >
                                <Sun size={16} />
                                <span>亮色</span>
                            </button>
                            <button
                                className={`theme-option ${theme === 'dark' ? 'theme-option--active' : ''}`}
                                onClick={() => handleThemeChange('dark')}
                            >
                                <Moon size={16} />
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
                                Knowledge Keeper 是一个智能知识管理工具，帮助你收集、整理和检索知识。
                                支持网页收藏、笔记记录、文件上传，并通过 AI 自动生成摘要和标签。
                                基于向量搜索实现语义检索，让你的知识触手可及。
                            </p>
                            <div className="settings-about__links">
                                <a
                                    href="https://github.com/zoglmk/knowledge-keeper"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="settings-about__link"
                                >
                                    <Github size={18} />
                                    GitHub
                                    <ExternalLink size={14} />
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
