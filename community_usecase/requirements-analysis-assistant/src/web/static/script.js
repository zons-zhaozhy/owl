// DOM元素
const elements = {
    analyzeBtn: document.getElementById('analyzeBtn'),
    requirementText: document.getElementById('requirementText'),
    loading: document.getElementById('loading'),
    results: document.getElementById('results')
};

// 状态管理
let isAnalyzing = false;

// 事件监听器
elements.analyzeBtn.addEventListener('click', handleAnalyzeClick);
elements.requirementText.addEventListener('keydown', handleKeyDown);

// 主要分析函数
async function handleAnalyzeClick() {
    const text = elements.requirementText.value.trim();
    if (!text) {
        showNotification('请输入需求描述', 'error');
        return;
    }

    if (isAnalyzing) {
        return;
    }

    try {
        isAnalyzing = true;
        showLoading(true);
        
        const data = await analyzeRequirements(text);
        updateResults(data);
        showNotification('分析完成', 'success');
        
    } catch (error) {
        console.error('分析错误:', error);
        showNotification('分析过程出错: ' + error.message, 'error');
    } finally {
        isAnalyzing = false;
        showLoading(false);
    }
}

// 键盘事件处理
function handleKeyDown(event) {
    if (event.ctrlKey && event.key === 'Enter') {
        handleAnalyzeClick();
    }
}

// API请求
async function analyzeRequirements(text) {
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    });

    if (!response.ok) {
        throw new Error(await response.text() || '分析请求失败');
    }

    return await response.json();
}

// UI更新函数
function showLoading(show) {
    elements.loading.classList.toggle('hidden', !show);
    elements.results.classList.toggle('hidden', show);
    elements.analyzeBtn.disabled = show;
    elements.analyzeBtn.textContent = show ? '分析中...' : '开始分析';
}

function updateResults(data) {
    // 更新需求提取结果
    updateList('functionalRequirements', data.requirements.functional_requirements);
    updateList('nonFunctionalRequirements', data.requirements.non_functional_requirements);
    updateList('constraints', data.requirements.constraints);

    // 更新需求分析结果
    updateList('technicalFeasibility', data.analysis.technical_feasibility);
    updateList('resourceRequirements', data.analysis.resource_requirements);
    updateList('riskAnalysis', data.analysis.risk_analysis);

    // 更新质量检查结果
    updateList('issues', data.quality_check.issues);
    updateList('recommendations', data.quality_check.recommendations);

    // 更新需求文档
    updateContent('projectOverview', data.documentation.project_overview);
    updateContent('requirementsList', data.documentation.requirements_list);
    updateContent('technicalSolution', data.documentation.technical_solution);
    updateContent('implementationPlan', data.documentation.implementation_plan);
    updateContent('riskManagement', data.documentation.risk_management);

    elements.results.classList.remove('hidden');
}

function updateList(elementId, items) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';
    
    if (items && items.length > 0) {
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            element.appendChild(li);
        });
    } else {
        element.innerHTML = '<li class="text-gray-400">无数据</li>';
    }
}

function updateContent(elementId, content) {
    const element = document.getElementById(elementId);
    element.innerHTML = '';

    if (content && content.length > 0) {
        content.forEach(item => {
            const p = document.createElement('p');
            p.textContent = item;
            p.className = 'mb-2';
            element.appendChild(p);
        });
    } else {
        element.innerHTML = '<p class="text-gray-400">无数据</p>';
    }
}

// 通知系统
function showNotification(message, type = 'info') {
    // 检查是否已存在通知容器
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container fixed top-4 right-4 z-50';
        document.body.appendChild(container);
    }

    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification p-4 mb-4 rounded-lg shadow-lg transform translate-x-full transition-all duration-300 ease-out`;
    
    // 设置通知样式
    switch (type) {
        case 'success':
            notification.classList.add('bg-green-500', 'text-white');
            break;
        case 'error':
            notification.classList.add('bg-red-500', 'text-white');
            break;
        case 'warning':
            notification.classList.add('bg-yellow-500', 'text-white');
            break;
        default:
            notification.classList.add('bg-blue-500', 'text-white');
    }

    // 设置通知内容
    notification.textContent = message;

    // 添加到容器
    container.appendChild(notification);

    // 触发动画
    requestAnimationFrame(() => {
        notification.classList.remove('translate-x-full');
    });

    // 自动移除
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            container.removeChild(notification);
            if (container.children.length === 0) {
                document.body.removeChild(container);
            }
        }, 300);
    }, 3000);
}

// 导出功能
function exportResults() {
    const content = document.getElementById('results').cloneNode(true);
    
    // 移除不需要打印的元素
    content.querySelectorAll('.no-print').forEach(el => el.remove());
    
    // 创建打印窗口
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>需求分析报告</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <link href="/static/style.css" rel="stylesheet">
            <style>
                @media print {
                    body { padding: 20px; }
                    .page-break { page-break-before: always; }
                }
            </style>
        </head>
        <body>
            <h1 class="text-3xl font-bold mb-8">需求分析报告</h1>
            ${content.innerHTML}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
} 