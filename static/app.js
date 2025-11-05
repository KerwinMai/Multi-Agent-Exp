// ===== 全局状态管理 =====
const AppState = {
    userId: null,
    sessionId: null,
    isLoading: false,
    messageHistory: [],
    userInfo: null
};

// ===== API 配置 =====
const API_BASE_URL = window.location.origin;

// ===== API 调用函数 =====
async function apiCall(endpoint, data = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || '请求失败');
        }
        
        return result;
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// ===== 登录相关 =====
async function handleLogin() {
    const userIdInput = document.getElementById('userIdInput');
    const userId = userIdInput.value.trim() || 'guest';
    
    const loginBtn = document.getElementById('loginBtn');
    loginBtn.disabled = true;
    loginBtn.textContent = '登录中...';
    
    try {
        const result = await apiCall('login', { user_id: userId });
        
        if (result.success) {
            AppState.userId = result.user_id;
            AppState.sessionId = result.session_id;
            AppState.userInfo = result.user_info || null;
            
            // 隐藏登录页，显示主界面
            document.getElementById('loginOverlay').style.display = 'none';
            document.getElementById('mainApp').style.display = 'flex';
            
            // 更新用户信息显示
            updateUserInfo();
            
            // 显示欢迎消息
            addSystemMessage(`欢迎回来，${userId}！我已准备好为您服务。`);

            // 如果后端返回了长期记忆，提示已加载
            if (AppState.userInfo) {
                const prefCount = AppState.userInfo.preferences ? Object.keys(AppState.userInfo.preferences).length : 0;
                const knowCount = Array.isArray(AppState.userInfo.knowledge) ? AppState.userInfo.knowledge.length : 0;
                if (prefCount > 0 || knowCount > 0) {
                    addSystemMessage(`已加载您的长期记忆：偏好 ${prefCount} 项，知识 ${knowCount} 条。`);
                }
            }
        }
    } catch (error) {
        alert('登录失败: ' + error.message);
        loginBtn.disabled = false;
        loginBtn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            开始使用
        `;
    }
}

function updateUserInfo() {
    document.getElementById('userName').textContent = AppState.userId || 'Guest';
    document.getElementById('sessionId').textContent = 
        AppState.sessionId ? AppState.sessionId.substring(0, 8) + '...' : '-';
}

function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
        location.reload();
    }
}

// ===== Markdown 渲染 =====
function renderMarkdown(mdText) {
    try {
        if (typeof marked !== 'undefined') {
            if (!window.__markedConfigured) {
                marked.setOptions({
                    gfm: true,
                    breaks: true,
                    mangle: false,
                    headerIds: false,
                    highlight: function(code, lang) {
                        try {
                            if (typeof hljs !== 'undefined') {
                                if (lang && hljs.getLanguage(lang)) {
                                    return hljs.highlight(code, { language: lang }).value;
                                }
                                return hljs.highlightAuto(code).value;
                            }
                        } catch (e) {
                            // ignore highlight errors
                        }
                        return code;
                    }
                });
                window.__markedConfigured = true;
            }
            let html = marked.parse(mdText);
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html);
            }
            return html;
        }
    } catch (e) {
        console.warn('Markdown 渲染失败，回退为纯文本:', e);
    }
    return escapeHtml(mdText);
}

// ===== 消息相关 =====
function addMessage(text, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 移除欢迎消息
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    const bubbleInner = isUser 
        ? `${escapeHtml(text)}`
        : `<div class="markdown-body">${renderMarkdown(text)}</div>`;

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${isUser 
                    ? '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'
                    : '<path d="M12 2L2 7L12 12L22 7L12 2Z"/><path d="M2 17L12 22L22 17"/><path d="M2 12L12 17L22 12"/>'
                }
            </svg>
        </div>
        <div class="message-content">
            <div class="message-bubble">${bubbleInner}</div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 代码高亮（仅对AI消息）
    if (!isUser && typeof hljs !== 'undefined') {
        messageDiv.querySelectorAll('pre code').forEach(block => {
            try { hljs.highlightElement(block); } catch (e) {}
        });
    }
    
    // 保存到历史
    AppState.messageHistory.push({ text, isUser, time: timeStr });
}

function addSystemMessage(text) {
    addMessage('ℹ️ ' + text, false);
}

function showLoading() {
    const chatMessages = document.getElementById('chatMessages');
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loadingMessage';
    
    loadingDiv.innerHTML = `
        <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                <path d="M2 17L12 22L22 17"/>
                <path d="M2 12L12 17L22 12"/>
            </svg>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="loading-indicator">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideLoading() {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ===== 查询处理 =====
async function handleQuery(question) {
    if (!question.trim()) return;
    
    if (AppState.isLoading) {
        alert('请等待当前查询完成');
        return;
    }
    
    AppState.isLoading = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    
    // 显示用户消息
    addMessage(question, true);
    
    // 显示加载动画
    showLoading();
    
    try {
        const result = await apiCall('query', {
            user_id: AppState.userId,
            question: question
        });
        
        hideLoading();
        
        if (result.success) {
            addMessage(result.answer, false);
        } else {
            addMessage('抱歉，查询失败：' + (result.error || '未知错误'), false);
        }
    } catch (error) {
        hideLoading();
        addMessage('抱歉，发生错误：' + error.message, false);
    } finally {
        AppState.isLoading = false;
        sendBtn.disabled = false;
    }
}

function handleSend() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (question) {
        handleQuery(question);
        input.value = '';
        input.style.height = 'auto';
    }
}

// ===== 会话管理 =====
async function handleNewSession() {
    if (!confirm('确定要开始新会话吗？当前对话历史将被清空（您的长期记忆会保留）。')) {
        return;
    }
    
    try {
        const result = await apiCall('new_session', {
            user_id: AppState.userId
        });
        
        if (result.success) {
            AppState.sessionId = result.session_id;
            AppState.messageHistory = [];
            
            // 清空聊天区域
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>🔄 新会话已开始</h2>
                    <p>您可以开始新的对话了。</p>
                </div>
            `;
            
            updateUserInfo();
            addSystemMessage('新会话已创建，会话ID: ' + result.session_id.substring(0, 8) + '...');
        }
    } catch (error) {
        alert('创建新会话失败: ' + error.message);
    }
}

// ===== 用户信息 =====
async function handleShowUserInfo() {
    try {
        // 优先使用登录时返回的缓存，必要时刷新
        let userInfo = AppState.userInfo;
        if (!userInfo) {
            const result = await apiCall('user_info', { user_id: AppState.userId });
            if (result.success) {
                userInfo = result.user_info;
                AppState.userInfo = userInfo;
            }
        }
        
        if (userInfo) {
            const modal = document.getElementById('userInfoModal');
            const content = document.getElementById('userInfoContent');
            
            // 构建用户信息HTML
            let html = `
                <div class="info-item">
                    <div class="info-label">用户ID</div>
                    <div class="info-value">${userInfo.user_id || '-'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">会话ID</div>
                    <div class="info-value">${userInfo.session_id || '-'}</div>
                </div>
            `;

            // 用户档案
            if (userInfo.profile) {
                html += `
                    <div class="info-item">
                        <div class="info-label">创建时间</div>
                        <div class="info-value">${userInfo.profile.created_at || '-'}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">最后活跃</div>
                        <div class="info-value">${userInfo.profile.last_active || '-'}</div>
                    </div>
                `;
            }
            
            // 显示用户偏好
            if (userInfo.preferences && Object.keys(userInfo.preferences).length > 0) {
                html += `
                    <div class="info-item">
                        <div class="info-label">用户偏好</div>
                        <ul class="preferences-list">
                `;
                
                for (const [key, value] of Object.entries(userInfo.preferences)) {
                    html += `<li><strong>${key}:</strong> ${value}</li>`;
                }
                
                html += `</ul></div>`;
            } else {
                html += `
                    <div class="info-item">
                        <div class="info-label">用户偏好</div>
                        <div class="info-value" style="color: var(--text-tertiary);">
                            暂无偏好记录。继续使用系统，我们会自动学习您的偏好。
                        </div>
                    </div>
                `;
            }

            // 知识列表
            const knowledge = Array.isArray(userInfo.knowledge) ? userInfo.knowledge : [];
            if (knowledge.length > 0) {
                html += `
                    <div class="info-item">
                        <div class="info-label">用户知识（最近${knowledge.length}条）</div>
                        <ul class="preferences-list">
                `;
                knowledge.slice(0, 20).forEach(k => {
                    const summary = (k.content || '').length > 120 ? (k.content.slice(0, 120) + '...') : (k.content || '');
                    html += `<li><strong>${k.category || '知识'}:</strong> ${summary}</li>`;
                });
                html += `</ul></div>`;
            }
            
            content.innerHTML = html;
            modal.classList.add('active');
        }
    } catch (error) {
        alert('获取用户信息失败: ' + error.message);
    }
}

function handleCloseModal() {
    const modal = document.getElementById('userInfoModal');
    modal.classList.remove('active');
}

// ===== 快捷问题 =====
function handleQuickQuestion(question) {
    const input = document.getElementById('questionInput');
    input.value = question;
    input.focus();
}

// ===== 事件监听器 =====
document.addEventListener('DOMContentLoaded', () => {
    // 登录相关
    const userIdInput = document.getElementById('userIdInput');
    const loginBtn = document.getElementById('loginBtn');
    
    userIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });
    
    loginBtn.addEventListener('click', handleLogin);
    
    // 主界面按钮
    document.getElementById('sendBtn').addEventListener('click', handleSend);
    document.getElementById('newSessionBtn').addEventListener('click', handleNewSession);
    document.getElementById('userInfoBtn').addEventListener('click', handleShowUserInfo);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('closeModalBtn').addEventListener('click', handleCloseModal);
    
    // 输入框处理
    const questionInput = document.getElementById('questionInput');
    
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // 自动调整输入框高度
    questionInput.addEventListener('input', () => {
        questionInput.style.height = 'auto';
        questionInput.style.height = questionInput.scrollHeight + 'px';
    });
    
    // 快速问题点击
    document.querySelectorAll('.question-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.getAttribute('data-question');
            handleQuickQuestion(question);
        });
    });
    
    // 模态框点击外部关闭
    const modal = document.getElementById('userInfoModal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            handleCloseModal();
        }
    });
    
    // 聚焦到用户ID输入框
    userIdInput.focus();
});

// ===== 工具函数 =====
function formatTimestamp(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// ===== 导出API供控制台调试 =====
window.AppDebug = {
    state: AppState,
    apiCall,
    handleQuery,
    handleNewSession
};

console.log('🚀 多智能体数据查询系统前端已加载');
console.log('💡 提示：可以通过 window.AppDebug 访问调试API');

