// DOM元素
const form = document.getElementById('requirementsForm');
const textarea = document.getElementById('requirements');
const results = document.getElementById('results');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = error.querySelector('.message');
const resultSections = document.querySelectorAll('.result-section');

// 常量
const API_URL = '/api/analyze';
const SECTIONS = [
    '需求概述',
    '功能需求列表',
    '非功能需求',
    '约束条件',
    '风险分析',
    '建议和建议'
];

// 工具函数
function showLoading() {
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    error.classList.add('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showError(message) {
    error.classList.remove('hidden');
    errorMessage.textContent = message;
    error.classList.add('error-shake');
    setTimeout(() => {
        error.classList.remove('error-shake');
    }, 1000);
}

function showResults(data) {
    results.classList.remove('hidden');
    
    // 清空所有结果区域
    resultSections.forEach(section => {
        section.classList.add('hidden');
        section.classList.remove('show');
    });
    
    // 填充结果
    Object.entries(data.analysis).forEach(([key, value], index) => {
        const section = resultSections[index];
        if (section) {
            const content = section.querySelector('.content');
            content.textContent = value;
            
            // 显示区域并添加动画
            section.classList.remove('hidden');
            setTimeout(() => {
                section.classList.add('show');
            }, index * 100);
        }
    });
}

// 表单提交处理
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const requirements = textarea.value.trim();
    if (!requirements) {
        showError('请输入需求描述');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: requirements
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        showResults(data);
    } catch (err) {
        showError('需求分析失败：' + err.message);
    } finally {
        hideLoading();
    }
});

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter 提交表单
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        form.dispatchEvent(new Event('submit'));
    }
});

// 自动调整文本框高度
textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 聚焦到文本框
    textarea.focus();
    
    // 检查是否支持 Fetch API
    if (!window.fetch) {
        showError('您的浏览器不支持现代Web功能，请升级到最新版本');
    }
}); 