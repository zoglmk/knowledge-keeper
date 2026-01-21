/**
 * 搜索页面组件
 */

import React, { useState } from 'react';
import {
    Search as SearchIcon,
    Filter,
    Link,
    FileText,
    File,
    ExternalLink,
    Database,
    Loader2,
    X,
} from 'lucide-react';
import { searchApi } from '../../services/api';
import type { SearchResult } from '../../services/api';
import { useAppStore } from '../../stores';
import './Search.css';

// 搜索结果卡片
const ResultCard: React.FC<{ result: SearchResult }> = ({ result }) => {
    const { bookmark, relevance, highlight } = result;

    const getTypeIcon = () => {
        switch (bookmark.type) {
            case 'url':
                return <Link size={16} />;
            case 'note':
                return <FileText size={16} />;
            case 'file':
                return <File size={16} />;
        }
    };

    return (
        <div className="result-card">
            <div className="result-card__header">
                <div className="result-card__type">{getTypeIcon()}</div>
                <div className="result-card__info">
                    <h3 className="result-card__title">{bookmark.title}</h3>
                    {bookmark.url && (
                        <a
                            href={bookmark.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="result-card__url"
                        >
                            {new URL(bookmark.url).hostname}
                            <ExternalLink size={12} />
                        </a>
                    )}
                </div>
                <div className="result-card__relevance">
                    <span className="result-card__relevance-value">
                        {Math.round(relevance * 100)}%
                    </span>
                    <span className="result-card__relevance-label">相关度</span>
                </div>
            </div>

            {(highlight || bookmark.summary) && (
                <p className="result-card__content">
                    {highlight || bookmark.summary}
                </p>
            )}

            <div className="result-card__tags">
                {bookmark.tags.slice(0, 4).map((tag) => (
                    <span
                        key={tag.id}
                        className="tag"
                        style={{ background: `${tag.color}20`, color: tag.color }}
                    >
                        {tag.name}
                    </span>
                ))}
            </div>
        </div>
    );
};

const Search: React.FC = () => {
    const { showNotification } = useAppStore();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    // 筛选选项
    const [useSemantic, setUseSemantic] = useState(true);
    const [filterType, setFilterType] = useState<string>('');

    const handleSearch = async (e?: React.FormEvent) => {
        e?.preventDefault();

        if (!query.trim()) return;

        setLoading(true);
        setHasSearched(true);

        try {
            const res = await searchApi.search({
                q: query.trim(),
                use_semantic: useSemantic,
                type: filterType || undefined,
            });
            setResults(res.results);
            setTotal(res.total);
        } catch (error: any) {
            showNotification('error', '搜索失败');
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const clearSearch = () => {
        setQuery('');
        setResults([]);
        setHasSearched(false);
    };

    return (
        <div className="search-page">
            {/* 搜索头部 */}
            <header className="search-page__header">
                <h1>搜索知识库</h1>
                <p>在你的收藏中搜索，支持关键词和语义搜索</p>
            </header>

            {/* 搜索框 */}
            <form className="search-page__form" onSubmit={handleSearch}>
                <div className="search-page__input-wrapper">
                    <SearchIcon size={20} />
                    <input
                        type="text"
                        placeholder="输入关键词或问题..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        autoFocus
                    />
                    {query && (
                        <button type="button" className="search-page__clear" onClick={clearSearch}>
                            <X size={18} />
                        </button>
                    )}
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? <Loader2 size={18} className="animate-spin" /> : '搜索'}
                    </button>
                </div>

                {/* 筛选选项 */}
                <div className="search-page__filters">
                    <label className="search-page__filter-toggle">
                        <input
                            type="checkbox"
                            checked={useSemantic}
                            onChange={(e) => setUseSemantic(e.target.checked)}
                        />
                        <Database size={16} />
                        <span>语义搜索</span>
                    </label>

                    <div className="search-page__filter-group">
                        <Filter size={16} />
                        <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <option value="">全部类型</option>
                            <option value="url">网页</option>
                            <option value="note">笔记</option>
                            <option value="file">文件</option>
                        </select>
                    </div>
                </div>
            </form>

            {/* 搜索结果 */}
            <div className="search-page__results">
                {loading ? (
                    <div className="search-page__loading">
                        <Loader2 size={32} className="animate-spin" />
                        <span>搜索中...</span>
                    </div>
                ) : hasSearched ? (
                    results.length === 0 ? (
                        <div className="search-page__empty">
                            <SearchIcon size={48} />
                            <h3>未找到相关结果</h3>
                            <p>尝试使用不同的关键词或开启语义搜索</p>
                        </div>
                    ) : (
                        <>
                            <div className="search-page__results-header">
                                <span>找到 <strong>{total}</strong> 个结果</span>
                            </div>
                            <div className="search-page__results-list">
                                {results.map((result) => (
                                    <ResultCard key={result.bookmark.id} result={result} />
                                ))}
                            </div>
                        </>
                    )
                ) : (
                    <div className="search-page__placeholder">
                        <div className="search-page__placeholder-icon">
                            <SearchIcon size={48} />
                        </div>
                        <h3>开始搜索</h3>
                        <p>输入关键词搜索你的知识库</p>
                        <div className="search-page__tips">
                            <div className="search-page__tip">
                                <strong>💡 提示：</strong>
                                开启语义搜索可以找到意思相近但用词不同的内容
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Search;
