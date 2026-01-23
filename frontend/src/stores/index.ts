/**
 * 全局状态管理
 */

import { create } from 'zustand';
import type { Bookmark, Tag, Conversation } from '../services/api';

// ==================== 应用状态 ====================

interface AppState {
    // 侧边栏状态
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    toggleSidebar: () => void;

    // 当前视图（包含基础视图和本地私有视图）
    currentView: 'home' | 'bookmarks' | 'chat' | 'search' | 'settings' | 'wechat';
    setCurrentView: (view: AppState['currentView']) => void;

    // 加载状态
    isLoading: boolean;
    setIsLoading: (loading: boolean) => void;

    // 通知
    notification: { type: 'success' | 'error' | 'info'; message: string } | null;
    showNotification: (type: 'success' | 'error' | 'info', message: string) => void;
    clearNotification: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    // 移动端默认关闭侧边栏
    sidebarOpen: typeof window !== 'undefined' ? window.innerWidth > 768 : true,
    setSidebarOpen: (open) => set({ sidebarOpen: open }),
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    currentView: 'home',
    setCurrentView: (view) => set({ currentView: view }),

    isLoading: false,
    setIsLoading: (loading) => set({ isLoading: loading }),

    notification: null,
    showNotification: (type, message) => {
        set({ notification: { type, message } });
        // 3秒后自动清除
        setTimeout(() => set({ notification: null }), 3000);
    },
    clearNotification: () => set({ notification: null }),
}));

// ==================== 收藏状态 ====================

interface BookmarkState {
    bookmarks: Bookmark[];
    setBookmarks: (bookmarks: Bookmark[]) => void;
    addBookmark: (bookmark: Bookmark) => void;
    updateBookmark: (id: string, data: Partial<Bookmark>) => void;
    removeBookmark: (id: string) => void;

    selectedBookmark: Bookmark | null;
    setSelectedBookmark: (bookmark: Bookmark | null) => void;

    // 筛选
    filterTag: string | null;
    setFilterTag: (tag: string | null) => void;
    filterType: string | null;
    setFilterType: (type: string | null) => void;
}

export const useBookmarkStore = create<BookmarkState>((set) => ({
    bookmarks: [],
    setBookmarks: (bookmarks) => set({ bookmarks }),
    addBookmark: (bookmark) =>
        set((state) => ({ bookmarks: [bookmark, ...state.bookmarks] })),
    updateBookmark: (id, data) =>
        set((state) => ({
            bookmarks: state.bookmarks.map((b) => (b.id === id ? { ...b, ...data } : b)),
        })),
    removeBookmark: (id) =>
        set((state) => ({
            bookmarks: state.bookmarks.filter((b) => b.id !== id),
        })),

    selectedBookmark: null,
    setSelectedBookmark: (bookmark) => set({ selectedBookmark: bookmark }),

    filterTag: null,
    setFilterTag: (tag) => set({ filterTag: tag }),
    filterType: null,
    setFilterType: (type) => set({ filterType: type }),
}));

// ==================== 标签状态 ====================

interface TagState {
    tags: Tag[];
    setTags: (tags: Tag[]) => void;
    addTag: (tag: Tag) => void;
    updateTag: (id: string, data: Partial<Tag>) => void;
    removeTag: (id: string) => void;
}

export const useTagStore = create<TagState>((set) => ({
    tags: [],
    setTags: (tags) => set({ tags }),
    addTag: (tag) => set((state) => ({ tags: [...state.tags, tag] })),
    updateTag: (id, data) =>
        set((state) => ({
            tags: state.tags.map((t) => (t.id === id ? { ...t, ...data } : t)),
        })),
    removeTag: (id) =>
        set((state) => ({
            tags: state.tags.filter((t) => t.id !== id),
        })),
}));

// ==================== 对话状态 ====================

interface ChatState {
    conversations: Conversation[];
    setConversations: (conversations: Conversation[]) => void;
    addConversation: (conversation: Conversation) => void;
    removeConversation: (id: string) => void;

    currentConversation: Conversation | null;
    setCurrentConversation: (conversation: Conversation | null) => void;

    // 输入框内容
    inputMessage: string;
    setInputMessage: (message: string) => void;

    // 是否使用知识库
    useKnowledgeBase: boolean;
    setUseKnowledgeBase: (use: boolean) => void;

    // 发送中状态
    isSending: boolean;
    setIsSending: (sending: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
    conversations: [],
    setConversations: (conversations) => set({ conversations }),
    addConversation: (conversation) =>
        set((state) => ({ conversations: [conversation, ...state.conversations] })),
    removeConversation: (id) =>
        set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== id),
        })),

    currentConversation: null,
    setCurrentConversation: (conversation) => set({ currentConversation: conversation }),

    inputMessage: '',
    setInputMessage: (message) => set({ inputMessage: message }),

    useKnowledgeBase: true,
    setUseKnowledgeBase: (use) => set({ useKnowledgeBase: use }),

    isSending: false,
    setIsSending: (sending) => set({ isSending: sending }),
}));

// ==================== 后台任务状态 ====================

interface TaskState {
    // 正在添加的任务数
    pendingAddCount: number;
    incrementPendingAdd: () => void;
    decrementPendingAdd: () => void;

    // 正在刷新的收藏 ID 集合
    refreshingIds: Set<string>;
    addRefreshingId: (id: string) => void;
    removeRefreshingId: (id: string) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
    pendingAddCount: 0,
    incrementPendingAdd: () => set((state) => ({ pendingAddCount: state.pendingAddCount + 1 })),
    decrementPendingAdd: () => set((state) => ({ pendingAddCount: Math.max(0, state.pendingAddCount - 1) })),

    refreshingIds: new Set(),
    addRefreshingId: (id) => set((state) => {
        const newSet = new Set(state.refreshingIds);
        newSet.add(id);
        return { refreshingIds: newSet };
    }),
    removeRefreshingId: (id) => set((state) => {
        const newSet = new Set(state.refreshingIds);
        newSet.delete(id);
        return { refreshingIds: newSet };
    }),
}));
