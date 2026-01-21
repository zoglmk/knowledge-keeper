/**
 * 聊天页面组件 - 支持流式输出
 */

import React, { useEffect, useRef, useState } from 'react';
import {
    Send,
    Plus,
    MessageSquare,
    Trash2,
    BookOpen,
    ExternalLink,
    Loader2,
    Sparkles,
    Database,
    X,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatApi, bookmarkApi } from '../../services/api';
import type { Conversation, Message, SourceReference } from '../../services/api';
import { useChatStore, useAppStore } from '../../stores';
import './Chat.css';

// 临时消息类型（用于流式输出）
interface TempMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceReference[];
    isStreaming?: boolean;
}

// 消息气泡组件
const MessageBubble: React.FC<{
    message: Message | TempMessage;
    sources?: SourceReference[];
    isStreaming?: boolean;
    onSourceClick?: (source: SourceReference) => void;
}> = ({ message, sources, isStreaming, onSourceClick }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`message ${isUser ? 'message--user' : 'message--assistant'}`}>
            <div className="message__avatar">
                {isUser ? '👤' : <Sparkles size={20} />}
            </div>
            <div className="message__content">
                <div className={`message__bubble ${isStreaming ? 'message__bubble--streaming' : ''}`}>
                    {isUser ? (
                        <p>{message.content}</p>
                    ) : (
                        <>
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                            {isStreaming && <span className="message__cursor">▊</span>}
                        </>
                    )}
                </div>

                {/* 来源引用 */}
                {!isUser && sources && sources.length > 0 && (
                    <div className="message__sources">
                        <div className="message__sources-header">
                            <BookOpen size={14} />
                            <span>参考来源</span>
                        </div>
                        <div className="message__sources-list">
                            {sources.map((source, idx) => (
                                <div
                                    key={idx}
                                    className="message__source-item message__source-item--clickable"
                                    onClick={() => onSourceClick?.(source)}
                                >
                                    <span className="message__source-title">{source.title}</span>
                                    <span className="message__source-relevance">
                                        {Math.round(source.relevance * 100)}%
                                    </span>
                                    {source.url && (
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="message__source-link"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            <ExternalLink size={12} />
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// 对话列表项
const ConversationItem: React.FC<{
    conversation: Conversation;
    isActive: boolean;
    onClick: () => void;
    onDelete: () => void;
}> = ({ conversation, isActive, onClick, onDelete }) => {
    return (
        <div
            className={`conversation-item ${isActive ? 'conversation-item--active' : ''}`}
            onClick={onClick}
        >
            <MessageSquare size={18} />
            <span className="conversation-item__title">{conversation.title}</span>
            <button
                className="conversation-item__delete"
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                }}
            >
                <Trash2 size={14} />
            </button>
        </div>
    );
};

const Chat: React.FC = () => {
    const {
        conversations,
        setConversations,
        currentConversation,
        setCurrentConversation,
        addConversation,
        removeConversation,
        inputMessage,
        setInputMessage,
        useKnowledgeBase,
        setUseKnowledgeBase,
        isSending,
        setIsSending,
    } = useChatStore();

    const { showNotification } = useAppStore();
    const [loading, setLoading] = useState(true);
    const [streamingMessage, setStreamingMessage] = useState<TempMessage | null>(null);
    const [pendingUserMessage, setPendingUserMessage] = useState<TempMessage | null>(null);
    const [streamSources, setStreamSources] = useState<SourceReference[]>([]);
    const [selectedSource, setSelectedSource] = useState<SourceReference | null>(null);
    const [sourceDetail, setSourceDetail] = useState<any>(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // 加载对话列表
    useEffect(() => {
        loadConversations();
    }, []);

    // 滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [currentConversation?.messages, streamingMessage]);

    const loadConversations = async () => {
        try {
            const res = await chatApi.listConversations();
            setConversations(res.items);
            if (res.items.length > 0 && !currentConversation) {
                setCurrentConversation(res.items[0]);
            }
        } catch (error) {
            console.error('加载对话列表失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNewConversation = () => {
        setCurrentConversation(null);
        setInputMessage('');
        inputRef.current?.focus();
    };

    const handleSelectConversation = async (conv: Conversation) => {
        try {
            const detail = await chatApi.getConversation(conv.id);
            setCurrentConversation(detail);
        } catch (error) {
            showNotification('error', '加载对话失败');
        }
    };

    const handleDeleteConversation = async (id: string) => {
        try {
            await chatApi.deleteConversation(id);
            removeConversation(id);
            if (currentConversation?.id === id) {
                setCurrentConversation(null);
            }
            showNotification('success', '对话已删除');
        } catch (error) {
            showNotification('error', '删除失败');
        }
    };

    // 处理来源点击
    const handleSourceClick = async (source: SourceReference) => {
        if (!source.bookmark_id) return;

        setSelectedSource(source);
        setLoadingDetail(true);

        try {
            const detail = await bookmarkApi.get(source.bookmark_id);
            setSourceDetail(detail);
        } catch (error) {
            showNotification('error', '加载详情失败');
            setSelectedSource(null);
        } finally {
            setLoadingDetail(false);
        }
    };

    const closeSourceDetail = () => {
        setSelectedSource(null);
        setSourceDetail(null);
    };

    const handleSendWithStream = async () => {
        if (!inputMessage.trim() || isSending) return;

        const message = inputMessage.trim();
        setInputMessage('');
        setIsSending(true);

        // 立即显示用户消息
        const userMsg: TempMessage = {
            id: 'temp-user-' + Date.now(),
            role: 'user',
            content: message,
        };
        setPendingUserMessage(userMsg);

        // 初始化流式消息
        setStreamingMessage({
            id: 'temp-assistant-' + Date.now(),
            role: 'assistant',
            content: '',
            isStreaming: true,
        });
        setStreamSources([]);

        try {
            const response = await fetch('http://localhost:8000/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    conversation_id: currentConversation?.id,
                    use_knowledge_base: useKnowledgeBase,
                }),
            });

            if (!response.ok) {
                throw new Error('请求失败');
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let conversationId = currentConversation?.id;

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));

                                if (data.type === 'conversation_id') {
                                    conversationId = data.data;
                                } else if (data.type === 'sources') {
                                    setStreamSources(data.data.map((s: any) => ({
                                        bookmark_id: s.bookmark_id,
                                        title: s.title,
                                        url: s.url,
                                        relevance: s.relevance,
                                        snippet: s.snippet,
                                    })));
                                } else if (data.type === 'content') {
                                    setStreamingMessage(prev => prev ? {
                                        ...prev,
                                        content: prev.content + data.data,
                                    } : null);
                                } else if (data.type === 'done') {
                                    // 流式输出完成，刷新对话
                                    if (conversationId) {
                                        const updated = await chatApi.getConversation(conversationId);
                                        if (!currentConversation) {
                                            addConversation(updated);
                                        }
                                        setCurrentConversation(updated);
                                    }
                                }
                            } catch (e) {
                                // 忽略解析错误
                            }
                        }
                    }
                }
            }
        } catch (error: any) {
            showNotification('error', error?.message || '发送失败');
            setInputMessage(message); // 恢复输入
        } finally {
            setIsSending(false);
            setStreamingMessage(null);
            setPendingUserMessage(null);
            setStreamSources([]);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendWithStream();
        }
    };

    // 合并显示的消息
    const displayMessages = () => {
        const messages: (Message | TempMessage)[] = currentConversation?.messages || [];
        const result = [...messages];

        // 添加待发送的用户消息
        if (pendingUserMessage) {
            result.push(pendingUserMessage);
        }

        return result;
    };

    return (
        <div className="chat-page">
            {/* 对话列表侧栏 */}
            <aside className="chat-page__sidebar">
                <button className="chat-page__new-btn" onClick={handleNewConversation}>
                    <Plus size={18} />
                    新对话
                </button>

                <div className="chat-page__conversations">
                    {loading ? (
                        <div className="chat-page__loading">
                            <Loader2 size={20} className="animate-spin" />
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="chat-page__empty">
                            <MessageSquare size={24} />
                            <span>暂无对话</span>
                        </div>
                    ) : (
                        conversations.map((conv) => (
                            <ConversationItem
                                key={conv.id}
                                conversation={conv}
                                isActive={currentConversation?.id === conv.id}
                                onClick={() => handleSelectConversation(conv)}
                                onDelete={() => handleDeleteConversation(conv.id)}
                            />
                        ))
                    )}
                </div>
            </aside>

            {/* 聊天主区域 */}
            <main className="chat-page__main">
                {/* 消息列表 */}
                <div className="chat-page__messages">
                    {displayMessages().length === 0 && !streamingMessage ? (
                        <div className="chat-page__welcome">
                            <div className="chat-page__welcome-icon">
                                <Sparkles size={48} />
                            </div>
                            <h2>开始智能对话</h2>
                            <p>向你的知识库提问，AI 会基于你收藏的内容为你解答</p>
                            <div className="chat-page__suggestions">
                                <button onClick={() => setInputMessage('帮我总结一下最近收藏的内容')}>
                                    帮我总结一下最近收藏的内容
                                </button>
                                <button onClick={() => setInputMessage('我收藏了哪些关于编程的文章？')}>
                                    我收藏了哪些关于编程的文章？
                                </button>
                                <button onClick={() => setInputMessage('根据我的笔记，解释一下...')}>
                                    根据我的笔记，解释一下...
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            {displayMessages().map((msg) => (
                                <MessageBubble
                                    key={msg.id}
                                    message={msg}
                                    sources={'sources' in msg ? msg.sources || undefined : undefined}
                                    onSourceClick={handleSourceClick}
                                />
                            ))}
                            {streamingMessage && (
                                <MessageBubble
                                    message={streamingMessage}
                                    sources={streamSources.length > 0 ? streamSources : undefined}
                                    isStreaming={true}
                                    onSourceClick={handleSourceClick}
                                />
                            )}
                        </>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* 输入区域 */}
                <div className="chat-page__input-area">
                    <div className="chat-page__input-options">
                        <label className="chat-page__toggle">
                            <input
                                type="checkbox"
                                checked={useKnowledgeBase}
                                onChange={(e) => setUseKnowledgeBase(e.target.checked)}
                            />
                            <Database size={16} />
                            <span>使用知识库</span>
                        </label>
                    </div>
                    <div className="chat-page__input-wrapper">
                        <textarea
                            ref={inputRef}
                            className="chat-page__input"
                            placeholder="输入你的问题..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSendWithStream();
                                }
                            }}
                            rows={1}
                            disabled={isSending}
                        />
                        <button
                            className="chat-page__send-btn"
                            onClick={handleSendWithStream}
                            disabled={!inputMessage.trim() || isSending}
                        >
                            {isSending ? (
                                <Loader2 size={20} className="animate-spin" />
                            ) : (
                                <Send size={20} />
                            )}
                        </button>
                    </div>
                </div>
            </main>

            {/* 来源详情弹窗 */}
            {selectedSource && (
                <div className="modal-overlay" onClick={closeSourceDetail}>
                    <div className="source-detail-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="source-detail-modal__header">
                            <h3>{selectedSource.title}</h3>
                            <button className="btn btn-ghost" onClick={closeSourceDetail}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="source-detail-modal__body">
                            {loadingDetail ? (
                                <div className="source-detail-modal__loading">
                                    <Loader2 size={24} className="animate-spin" />
                                    <span>加载中...</span>
                                </div>
                            ) : sourceDetail ? (
                                <>
                                    <div className="source-detail-modal__meta">
                                        <span className="source-detail-modal__relevance">
                                            相关度: {Math.round(selectedSource.relevance * 100)}%
                                        </span>
                                        {sourceDetail.url && (
                                            <a
                                                href={sourceDetail.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="source-detail-modal__url"
                                            >
                                                <ExternalLink size={14} />
                                                访问原文
                                            </a>
                                        )}
                                    </div>
                                    {sourceDetail.summary && (
                                        <div className="source-detail-modal__section">
                                            <h4>AI 摘要</h4>
                                            <p>{sourceDetail.summary}</p>
                                        </div>
                                    )}
                                    <div className="source-detail-modal__section">
                                        <h4>原文内容</h4>
                                        <div className="source-detail-modal__content">
                                            {sourceDetail.content || '无内容'}
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <p>无法加载详情</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Chat;
