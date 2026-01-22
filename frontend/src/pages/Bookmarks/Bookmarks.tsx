/**
 * 收藏页面组件
 */

import React, { useEffect, useState } from 'react';
import {
    Plus,
    Link,
    FileText,
    File,
    Search,
    MoreVertical,
    ExternalLink,
    Trash2,
    RefreshCw,
    X,
    Loader2,
    Sparkles,
} from 'lucide-react';
import { bookmarkApi, tagApi } from '../../services/api';
import type { Bookmark, CreateBookmarkData } from '../../services/api';
import { useBookmarkStore, useTagStore, useAppStore, useTaskStore } from '../../stores';
import './Bookmarks.css';

// 添加收藏弹窗
const AddBookmarkModal: React.FC<{
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (bookmark: Bookmark) => void;
    onStartPending?: () => void;
    onEndPending?: () => void;
}> = ({ isOpen, onClose, onSuccess, onStartPending, onEndPending }) => {
    const [type, setType] = useState<'url' | 'note' | 'file'>('url');
    const [url, setUrl] = useState('');
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [files, setFiles] = useState<File[]>([]);
    const [autoSummarize, setAutoSummarize] = useState(true);
    const [autoTag, setAutoTag] = useState(true);
    const [loading, setLoading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<string>('');
    const { showNotification } = useAppStore();
    const fileInputRef = React.useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = Array.from(e.target.files || []);
        if (selectedFiles.length > 0) {
            setFiles(prev => [...prev, ...selectedFiles]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    // 后台处理上传
    const processInBackground = async () => {
        onStartPending?.();
        try {
            if (type === 'file' && files.length > 0) {
                if (files.length === 1) {
                    const formData = new FormData();
                    formData.append('file', files[0]);
                    if (title) formData.append('title', title);
                    formData.append('auto_summarize', String(autoSummarize));
                    formData.append('auto_tag', String(autoTag));

                    const response = await fetch('http://localhost:8000/api/bookmarks/upload', {
                        method: 'POST',
                        body: formData,
                    });

                    if (response.ok) {
                        const bookmark = await response.json();
                        showNotification('success', '文件上传成功！');
                        onSuccess(bookmark);
                    } else {
                        showNotification('error', '上传失败');
                    }
                } else {
                    const formData = new FormData();
                    files.forEach((file) => {
                        formData.append('files', file);
                    });
                    formData.append('auto_summarize', String(autoSummarize));
                    formData.append('auto_tag', String(autoTag));

                    const response = await fetch('http://localhost:8000/api/bookmarks/upload/batch', {
                        method: 'POST',
                        body: formData,
                    });

                    if (response.ok) {
                        const bookmarks = await response.json();
                        showNotification('success', `成功上传 ${bookmarks.length} 个文件！`);
                        if (bookmarks.length > 0) {
                            onSuccess(bookmarks[0]);
                        }
                    } else {
                        showNotification('error', '批量上传失败');
                    }
                }
            } else if (type === 'url' || type === 'note') {
                const data: CreateBookmarkData = {
                    type: type as 'url' | 'note',
                    auto_summarize: autoSummarize,
                    auto_tag: autoTag,
                };

                if (type === 'url') {
                    data.url = url;
                    if (title) data.title = title;
                } else {
                    data.title = title || '未命名笔记';
                    data.content = content;
                }

                const bookmark = await bookmarkApi.create(data);
                showNotification('success', '添加成功！');
                onSuccess(bookmark);
            }
        } catch (error: any) {
            showNotification('error', error?.response?.data?.detail || error?.message || '添加失败');
        } finally {
            onEndPending?.();
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // 立即关闭弹窗，后台处理
        onClose();
        resetForm();

        // 后台处理
        processInBackground();
    };

    const resetForm = () => {
        setUrl('');
        setTitle('');
        setContent('');
        setFiles([]);
        setUploadProgress('');
        setLoading(false);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // 处理关闭
    const handleClose = () => {
        resetForm();
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <h2>添加收藏</h2>
                    <button className="btn btn-ghost" onClick={handleClose}>
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    {/* 类型选择 */}
                    <div className="modal__type-tabs">
                        <button
                            type="button"
                            className={`modal__type-tab ${type === 'url' ? 'modal__type-tab--active' : ''}`}
                            onClick={() => setType('url')}
                        >
                            <Link size={18} />
                            网页链接
                        </button>
                        <button
                            type="button"
                            className={`modal__type-tab ${type === 'note' ? 'modal__type-tab--active' : ''}`}
                            onClick={() => setType('note')}
                        >
                            <FileText size={18} />
                            笔记
                        </button>
                        <button
                            type="button"
                            className={`modal__type-tab ${type === 'file' ? 'modal__type-tab--active' : ''}`}
                            onClick={() => setType('file')}
                        >
                            <File size={18} />
                            文件
                        </button>
                    </div>

                    {/* URL 输入 */}
                    {type === 'url' && (
                        <div className="form-group">
                            <label>网页链接</label>
                            <input
                                type="url"
                                className="input"
                                placeholder="https://example.com/article"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                required
                            />
                        </div>
                    )}

                    {/* 文件上传 */}
                    {type === 'file' && (
                        <div className="form-group">
                            <label>选择文件 <span className="text-muted">(支持多选)</span></label>
                            <div className="file-upload">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".txt,.md,.pdf,.doc,.docx,.html,.json"
                                    onChange={handleFileChange}
                                    className="file-upload__input"
                                    multiple
                                />
                                <div className="file-upload__box">
                                    <File size={24} />
                                    <span>点击或拖拽文件到这里</span>
                                    <span className="file-upload__hint">支持 TXT, MD, PDF, DOCX, HTML, JSON</span>
                                </div>
                            </div>
                            {/* 已选文件列表 */}
                            {files.length > 0 && (
                                <div className="file-upload__list">
                                    {files.map((f, index) => (
                                        <div key={index} className="file-upload__item">
                                            <File size={14} />
                                            <span className="file-upload__item-name">{f.name}</span>
                                            <span className="file-upload__item-size">
                                                {(f.size / 1024).toFixed(1)} KB
                                            </span>
                                            <button
                                                type="button"
                                                className="file-upload__item-remove"
                                                onClick={() => removeFile(index)}
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ))}
                                    <div className="file-upload__summary">
                                        共 {files.length} 个文件
                                    </div>
                                </div>
                            )}
                            {uploadProgress && (
                                <div className="file-upload__progress">
                                    <Loader2 size={16} className="animate-spin" />
                                    <span>{uploadProgress}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* 标题输入 */}
                    <div className="form-group">
                        <label>
                            标题
                            {type === 'url' && <span className="text-muted">(可选，自动提取)</span>}
                            {type === 'file' && <span className="text-muted">(可选，默认使用文件名)</span>}
                        </label>
                        <input
                            type="text"
                            className="input"
                            placeholder={type === 'url' ? '留空将自动提取' : type === 'file' ? '留空使用文件名' : '输入笔记标题'}
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required={type === 'note'}
                        />
                    </div>

                    {/* 内容输入 */}
                    {type === 'note' && (
                        <div className="form-group">
                            <label>内容</label>
                            <textarea
                                className="input textarea"
                                placeholder="输入笔记内容..."
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                rows={6}
                                required
                            />
                        </div>
                    )}

                    {/* AI 选项 */}
                    <div className="modal__options">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={autoSummarize}
                                onChange={(e) => setAutoSummarize(e.target.checked)}
                            />
                            <Sparkles size={16} />
                            AI 自动生成摘要
                        </label>
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={autoTag}
                                onChange={(e) => setAutoTag(e.target.checked)}
                            />
                            <Sparkles size={16} />
                            AI 自动生成标签
                        </label>
                    </div>

                    {/* 提交按钮 */}
                    <div className="modal__footer">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            取消
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? (
                                <>
                                    <Loader2 size={18} className="animate-spin" />
                                    处理中...
                                </>
                            ) : (
                                <>
                                    <Plus size={18} />
                                    添加
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// 收藏详情弹窗
const BookmarkDetailModal: React.FC<{
    bookmark: Bookmark | null;
    onClose: () => void;
}> = ({ bookmark, onClose }) => {
    if (!bookmark) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal--large" onClick={(e) => e.stopPropagation()}>
                <div className="modal__header">
                    <h2>{bookmark.title}</h2>
                    <button className="btn btn-ghost" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>
                <div className="modal__body">
                    {bookmark.url && (
                        <a
                            href={bookmark.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bookmark-detail__url"
                        >
                            <Link size={14} />
                            {bookmark.url}
                            <ExternalLink size={12} />
                        </a>
                    )}

                    {/* 标签 - 放在最上方 */}
                    {bookmark.tags.length > 0 && (
                        <div className="bookmark-detail__tags">
                            {bookmark.tags.map((tag) => (
                                <span
                                    key={tag.id}
                                    className="tag"
                                    style={{ background: `${tag.color}20`, color: tag.color }}
                                >
                                    {tag.name}
                                </span>
                            ))}
                        </div>
                    )}

                    {bookmark.summary && (
                        <div className="bookmark-detail__section">
                            <h4><Sparkles size={16} /> AI 摘要</h4>
                            <p>{bookmark.summary}</p>
                        </div>
                    )}

                    <div className="bookmark-detail__section">
                        <h4><FileText size={16} /> 原文内容</h4>
                        <div className="bookmark-detail__content">
                            {bookmark.content || '暂无内容'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// 收藏卡片
const BookmarkCard: React.FC<{
    bookmark: Bookmark;
    onDelete: (id: string) => void;
    onRefreshSummary: (id: string) => Promise<void>;
    onClick: () => void;
    isRefreshing?: boolean;
}> = ({ bookmark, onDelete, onRefreshSummary, onClick, isRefreshing }) => {
    const [showMenu, setShowMenu] = useState(false);
    const menuRef = React.useRef<HTMLDivElement>(null);

    // 点击外部关闭菜单
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setShowMenu(false);
            }
        };

        if (showMenu) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showMenu]);

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

    const formatDate = (date: string) => {
        return new Date(date).toLocaleDateString('zh-CN', {
            month: 'short',
            day: 'numeric',
        });
    };

    const handleRefresh = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowMenu(false);
        await onRefreshSummary(bookmark.id);
    };

    return (
        <div className="bookmark-card" onClick={onClick} style={{ cursor: 'pointer' }}>
            <div className="bookmark-card__header">
                <div className={`bookmark-card__type bookmark-card__type--${bookmark.type === 'url' ? 'webpage' : bookmark.type}`}>{getTypeIcon()}</div>
                <div className="bookmark-card__title-wrap">
                    <h3 className="bookmark-card__title">{bookmark.title}</h3>
                    {bookmark.url && (
                        <a
                            href={bookmark.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bookmark-card__url"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {new URL(bookmark.url).hostname}
                            <ExternalLink size={12} />
                        </a>
                    )}
                </div>
                <div className="bookmark-card__menu" ref={menuRef}>
                    <button
                        className="btn btn-ghost"
                        onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
                    >
                        <MoreVertical size={18} />
                    </button>
                    {showMenu && (
                        <div className="bookmark-card__dropdown">
                            <button onClick={handleRefresh}>
                                <RefreshCw size={16} />
                                重新生成摘要
                            </button>
                            <button
                                className="bookmark-card__dropdown-danger"
                                onClick={(e) => { e.stopPropagation(); setShowMenu(false); onDelete(bookmark.id); }}
                            >
                                <Trash2 size={16} />
                                删除
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {bookmark.summary && (
                <p className="bookmark-card__summary">{bookmark.summary}</p>
            )}

            <div className="bookmark-card__footer">
                <div className="bookmark-card__tags">
                    {isRefreshing ? (
                        <div className="bookmark-card__refreshing-inline">
                            <Loader2 size={14} className="animate-spin" />
                            <span>更新中...</span>
                        </div>
                    ) : (
                        <>
                            {bookmark.tags.slice(0, 3).map((tag) => (
                                <span
                                    key={tag.id}
                                    className="tag"
                                    style={{ background: `${tag.color}20`, color: tag.color }}
                                >
                                    {tag.name}
                                </span>
                            ))}
                            {bookmark.tags.length > 3 && (
                                <span className="tag">+{bookmark.tags.length - 3}</span>
                            )}
                        </>
                    )}
                </div>
                <span className="bookmark-card__date">{formatDate(bookmark.created_at)}</span>
            </div>
        </div>
    );
};


const Bookmarks: React.FC = () => {
    const { bookmarks, setBookmarks, addBookmark, removeBookmark, filterTag, setFilterTag } = useBookmarkStore();
    const { tags, setTags } = useTagStore();
    const { showNotification } = useAppStore();
    const { pendingAddCount, incrementPendingAdd, decrementPendingAdd, refreshingIds, addRefreshingId, removeRefreshingId } = useTaskStore();
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedBookmark, setSelectedBookmark] = useState<Bookmark | null>(null);

    useEffect(() => {
        loadData();
    }, [filterTag]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [bookmarkRes, tagsRes] = await Promise.all([
                bookmarkApi.list({ tag: filterTag || undefined }),
                tagApi.list(),
            ]);
            setBookmarks(bookmarkRes.items);
            setTags(tagsRes);
        } catch (error) {
            showNotification('error', '加载数据失败');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        try {
            await bookmarkApi.delete(id);
            removeBookmark(id);
            showNotification('success', '删除成功');
        } catch (error) {
            showNotification('error', '删除失败');
        }
    };

    const handleRefreshSummary = async (id: string) => {
        addRefreshingId(id);
        try {
            await bookmarkApi.regenerateSummary(id);
            await loadData(); // 重新加载数据
            showNotification('success', '摘要已更新');
        } catch (error) {
            showNotification('error', '生成摘要失败');
        } finally {
            removeRefreshingId(id);
        }
    };

    const filteredBookmarks = bookmarks.filter((b) =>
        b.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="bookmarks-page">
            {/* 头部 */}
            <header className="bookmarks-page__header">
                <div className="bookmarks-page__title-section">
                    <h1>我的收藏</h1>
                    <span className="bookmarks-page__count">{bookmarks.length} 项</span>
                </div>
                <div className="bookmarks-page__actions">
                    {pendingAddCount > 0 && (
                        <div className="bookmarks-page__pending">
                            <Loader2 size={16} className="animate-spin" />
                            <span>{pendingAddCount} 个添加中</span>
                        </div>
                    )}
                    <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
                        <Plus size={18} />
                        添加收藏
                    </button>
                </div>
            </header>

            {/* 筛选栏 */}
            <div className="bookmarks-page__filters">
                <div className="bookmarks-page__search">
                    <Search size={18} />
                    <input
                        type="text"
                        placeholder="搜索收藏..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="bookmarks-page__tags">
                    <button
                        className={`tag ${!filterTag ? 'tag--active' : ''}`}
                        onClick={() => setFilterTag(null)}
                    >
                        全部
                    </button>
                    {tags.slice(0, 8).map((tag) => (
                        <button
                            key={tag.id}
                            className={`tag ${filterTag === tag.name ? 'tag--active' : ''}`}
                            style={filterTag === tag.name ? { background: `${tag.color}30`, color: tag.color } : {}}
                            onClick={() => setFilterTag(tag.name)}
                        >
                            {tag.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* 收藏列表 */}
            <div className="bookmarks-page__grid">
                {loading ? (
                    <div className="bookmarks-page__loading">
                        <Loader2 size={32} className="animate-spin" />
                        <span>加载中...</span>
                    </div>
                ) : filteredBookmarks.length === 0 ? (
                    <div className="bookmarks-page__empty">
                        <FileText size={48} />
                        <h3>暂无收藏</h3>
                        <p>点击上方按钮添加你的第一个收藏</p>
                    </div>
                ) : (
                    filteredBookmarks.map((bookmark) => (
                        <BookmarkCard
                            key={bookmark.id}
                            bookmark={bookmark}
                            onDelete={handleDelete}
                            onRefreshSummary={handleRefreshSummary}
                            onClick={() => setSelectedBookmark(bookmark)}
                            isRefreshing={refreshingIds.has(bookmark.id)}
                        />
                    ))
                )}
            </div>

            {/* 添加弹窗 */}
            <AddBookmarkModal
                isOpen={showAddModal}
                onClose={() => setShowAddModal(false)}
                onSuccess={(bookmark) => { addBookmark(bookmark); loadData(); }}
                onStartPending={incrementPendingAdd}
                onEndPending={decrementPendingAdd}
            />

            {/* 详情弹窗 */}
            <BookmarkDetailModal
                bookmark={selectedBookmark}
                onClose={() => setSelectedBookmark(null)}
            />
        </div>
    );
};

export default Bookmarks;

