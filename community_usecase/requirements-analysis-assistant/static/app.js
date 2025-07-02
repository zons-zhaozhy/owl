// WebSocket连接
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// DOM元素
const messagesContainer = document.getElementById('messages');
const requirementsList = document.getElementById('requirements-list');
const analysisResult = document.getElementById('analysis-result');
const documentation = document.getElementById('documentation');
const input = document.getElementById('input');
const sendButton = document.getElementById('send-btn');

// 连接WebSocket
function connectWebSocket() {
    if (ws !== null) {
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        console.log('WebSocket连接已建立');
        reconnectAttempts = 0;
        addSystemMessage('系统已准备就绪，请输入您的需求。');
    };

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);
        handleResponse(response);
    };

    ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        ws = null;

        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
            setTimeout(connectWebSocket, delay);
        } else {
            addSystemMessage('连接已断开，请刷新页面重试。');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        addSystemMessage('连接发生错误，正在尝试重新连接...');
    };
}

// 发送消息
function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        addSystemMessage('正在建立连接，请稍候...');
        connectWebSocket();
        return;
    }

    // 发送需求文本
    ws.send(JSON.stringify({
        type: 'extract',
        text: text
    }));

    // 添加用户消息到聊天界面
    addUserMessage(text);
    input.value = '';
}

// 处理响应
function handleResponse(response) {
    switch (response.type) {
        case 'requirements':
            displayRequirements(response.data);
            // 自动请求分析
            ws.send(JSON.stringify({
                type: 'analyze',
                requirements: response.data
            }));
            break;

        case 'clarification':
            addAssistantMessage(response.question);
            break;

        case 'analysis':
            displayAnalysis(response.data);
            // 自动请求文档生成
            ws.send(JSON.stringify({
                type: 'document',
                requirements: response.data.requirements,
                analysis: response.data.analysis
            }));
            break;

        case 'documentation':
            displayDocumentation(response.data);
            break;

        case 'error':
            addSystemMessage(`错误: ${response.message}`);
            break;
    }
}

// 显示需求列表
function displayRequirements(requirements) {
    requirementsList.innerHTML = '';
    requirements.forEach((req, index) => {
        const reqElement = document.createElement('div');
        reqElement.className = 'requirement-item';
        reqElement.innerHTML = `
            <h4>需求 ${index + 1}</h4>
            <p>${req.description}</p>
            <div class="requirement-meta">
                <span class="priority ${req.priority.toLowerCase()}">${req.priority}</span>
                <span class="type">${req.type}</span>
            </div>
        `;
        requirementsList.appendChild(reqElement);
    });
}

// 显示分析结果
function displayAnalysis(analysis) {
    analysisResult.innerHTML = `
        <div class="analysis-section">
            <h4>功能分析</h4>
            <ul>
                ${analysis.functional_analysis.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
        <div class="analysis-section">
            <h4>技术约束</h4>
            <ul>
                ${analysis.technical_constraints.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
        <div class="analysis-section">
            <h4>风险评估</h4>
            <ul>
                ${analysis.risks.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
    `;
}

// 显示文档
function displayDocumentation(doc) {
    documentation.innerHTML = marked(doc);
}

// 添加消息到聊天界面
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addUserMessage(content) {
    addMessage(content, 'user');
}

function addAssistantMessage(content) {
    addMessage(content, 'assistant');
}

function addSystemMessage(content) {
    addMessage(content, 'system');
}

// 事件监听
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 初始化
connectWebSocket();

class RequirementsAnalyzer {
    constructor() {
        this.socket = null;
        this.isAnalyzing = false;
        this.initializeElements();
        this.initializeWebSocket();
        this.bindEvents();
    }

    initializeElements() {
        this.input = document.getElementById('requirements-input');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.statusIndicator = document.querySelector('.status-indicator');
        this.statusText = document.querySelector('.status-text');
        this.requirementsList = document.getElementById('requirements-list');
        this.analysisDetails = document.getElementById('analysis-details');
        this.qualityCheck = document.getElementById('quality-check');
    }

    initializeWebSocket() {
        this.socket = new WebSocket('ws://localhost:8000/ws');
        
        this.socket.onopen = () => {
            console.log('WebSocket连接已建立');
            this.updateStatus('就绪', 'success');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket连接已关闭');
            this.updateStatus('连接已断开', 'error');
            // 尝试重新连接
            setTimeout(() => this.initializeWebSocket(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.updateStatus('连接错误', 'error');
        };
    }

    bindEvents() {
        this.analyzeBtn.addEventListener('click', () => this.startAnalysis());
        this.input.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.startAnalysis();
            }
        });
    }

    startAnalysis() {
        if (this.isAnalyzing) return;
        
        const requirements = this.input.value.trim();
        if (!requirements) {
            this.showError('请输入需求描述');
            return;
        }

        this.isAnalyzing = true;
        this.updateStatus('正在分析...', 'loading');
        this.clearResults();
        this.analyzeBtn.disabled = true;

        this.socket.send(JSON.stringify({
            type: 'analyze',
            requirements: requirements
        }));
    }

    handleMessage(data) {
        switch (data.type) {
            case 'requirements':
                this.updateRequirements(data.content);
                break;
            case 'analysis':
                this.updateAnalysis(data.content);
                break;
            case 'quality':
                this.updateQuality(data.content);
                break;
            case 'complete':
                this.analysisComplete();
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }

    updateRequirements(content) {
        this.requirementsList.innerHTML = marked.parse(content);
    }

    updateAnalysis(content) {
        this.analysisDetails.innerHTML = marked.parse(content);
    }

    updateQuality(content) {
        this.qualityCheck.innerHTML = marked.parse(content);
    }

    analysisComplete() {
        this.isAnalyzing = false;
        this.analyzeBtn.disabled = false;
        this.updateStatus('分析完成', 'success');
    }

    showError(message) {
        this.isAnalyzing = false;
        this.analyzeBtn.disabled = false;
        this.updateStatus(message, 'error');
    }

    updateStatus(message, status) {
        this.statusText.textContent = message;
        this.statusIndicator.parentElement.className = 'analysis-status ' + status;
    }

    clearResults() {
        this.requirementsList.innerHTML = '';
        this.analysisDetails.innerHTML = '';
        this.qualityCheck.innerHTML = '';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RequirementsAnalyzer();
}); 