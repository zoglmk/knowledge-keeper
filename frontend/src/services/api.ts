/**
 * API 服务配置
 */

import axios from 'axios';

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// 创建 axios 实例
export const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        // 可以在这里添加认证 token
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

// ==================== 收藏相关 API ====================

export interface Tag {
    id: string;
    name: string;
    color: string;
    is_auto: boolean;
    usage_count: string;
    created_at: string;
}

export interface Bookmark {
    id: string;
    title: string;
    url: string | null;
    content: string | null;
    summary: string | null;
    type: 'url' | 'note' | 'file';
    is_embedded: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    tags: Tag[];
}

export interface BookmarkListResponse {
    items: Bookmark[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface CreateBookmarkData {
    title?: string;
    url?: string;
    content?: string;
    type: 'url' | 'note' | 'file';
    tags?: string[];
    auto_summarize?: boolean;
    auto_tag?: boolean;
}

export const bookmarkApi = {
    // 获取收藏列表
    list: (params?: { page?: number; page_size?: number; tag?: string; type?: string }) =>
        api.get<any, BookmarkListResponse>('/bookmarks', { params }),

    // 创建收藏
    create: (data: CreateBookmarkData) => api.post<any, Bookmark>('/bookmarks', data),

    // 获取收藏详情
    get: (id: string) => api.get<any, Bookmark>(`/bookmarks/${id}`),

    // 更新收藏
    update: (id: string, data: Partial<CreateBookmarkData>) =>
        api.put<any, Bookmark>(`/bookmarks/${id}`, data),

    // 删除收藏
    delete: (id: string) => api.delete(`/bookmarks/${id}`),

    // 重新生成摘要
    regenerateSummary: (id: string) =>
        api.post<any, Bookmark>(`/bookmarks/${id}/regenerate-summary`),
};

// ==================== 标签相关 API ====================

export const tagApi = {
    // 获取所有标签
    list: () => api.get<any, Tag[]>('/tags'),

    // 获取热门标签
    popular: (limit?: number) => api.get<any, Tag[]>('/tags/popular', { params: { limit } }),

    // 创建标签
    create: (data: { name: string; color?: string }) => api.post<any, Tag>('/tags', data),

    // 更新标签
    update: (id: string, data: { name: string; color?: string }) =>
        api.put<any, Tag>(`/tags/${id}`, data),

    // 删除标签
    delete: (id: string) => api.delete(`/tags/${id}`),
};

// ==================== 对话相关 API ====================

export interface SourceReference {
    bookmark_id: string;
    title: string;
    url: string | null;
    relevance: number;
    snippet: string | null;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    sources: SourceReference[] | null;
    created_at: string;
}

export interface Conversation {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    messages: Message[];
    message_count: number;
}

export interface ChatRequest {
    message: string;
    conversation_id?: string;
    use_knowledge_base?: boolean;
}

export interface ChatResponse {
    conversation_id: string;
    message: Message;
    sources: SourceReference[];
}

export const chatApi = {
    // 获取对话列表
    listConversations: () => api.get<any, { items: Conversation[]; total: number }>('/chat/conversations'),

    // 创建对话
    createConversation: (title?: string) =>
        api.post<any, Conversation>('/chat/conversations', { title }),

    // 获取对话详情
    getConversation: (id: string) => api.get<any, Conversation>(`/chat/conversations/${id}`),

    // 删除对话
    deleteConversation: (id: string) => api.delete(`/chat/conversations/${id}`),

    // 发送消息
    send: (data: ChatRequest) => api.post<any, ChatResponse>('/chat', data),
};

// ==================== 搜索相关 API ====================

export interface SearchResult {
    bookmark: Bookmark;
    relevance: number;
    highlight: string | null;
}

export interface SearchResponse {
    results: SearchResult[];
    total: number;
    query: string;
}

export interface SearchStats {
    total_bookmarks: number;
    by_type: Record<string, number>;
    total_tags: number;
    embedded_count: number;
    vector_collection: {
        name: string;
        count: number;
    };
}

export const searchApi = {
    // 搜索
    search: (params: {
        q: string;
        tags?: string;
        type?: string;
        use_semantic?: boolean;
        page?: number;
        page_size?: number;
    }) => api.get<any, SearchResponse>('/search', { params }),

    // 获取统计信息
    stats: () => api.get<any, SearchStats>('/search/stats'),
};
