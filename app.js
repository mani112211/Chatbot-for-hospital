// Global state
let hospitalInfo = {};
let allFaqs = [];
let chatHistory = [];

// DOM Elements
const faqAccordion = document.getElementById('faq-accordion');
const faqCategories = document.getElementById('faq-categories');
const faqSearch = document.getElementById('faq-search');
const clearSearchBtn = document.getElementById('clear-search');
const chatMessages = document.getElementById('chat-messages');
const chipsWrapper = document.getElementById('chips-wrapper');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const btnClearChat = document.getElementById('btn-clear');
const providerStatus = document.getElementById('provider-status');

// Helper: Format Markdown to HTML
function formatMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Bulleted Lists
    const lines = html.split('\n');
    let inList = false;
    let listHtml = [];
    
    for (let line of lines) {
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            if (!inList) {
                listHtml.push('<ul>');
                inList = true;
            }
            listHtml.push(`<li>${line.trim().substring(2)}</li>`);
        } else if (line.trim().match(/^\d+\.\s/)) {
            if (!inList) {
                listHtml.push('<ol>');
                inList = true;
            }
            const match = line.trim().match(/^\d+\.\s(.*)/);
            listHtml.push(`<li>${match[1]}</li>`);
        } else {
            if (inList) {
                listHtml.push(inList === 'ol' ? '</ol>' : '</ul>');
                inList = false;
            }
            listHtml.push(line);
        }
    }
    if (inList) {
        listHtml.push('</ul>');
    }
    
    return listHtml.join('\n').replace(/\n/g, '<br>');
}

// Initialise App
async function init() {
    try {
        const res = await fetch('/api/info');
        hospitalInfo = await res.json();
        allFaqs = hospitalInfo.faqs;
        
        // Update Static Details
        document.getElementById('bot-name').innerText = hospitalInfo.bot_name;
        document.getElementById('bot-tagline').innerText = hospitalInfo.bot_tagline;
        document.getElementById('hospital-address').innerText = hospitalInfo.address;
        document.getElementById('hospital-helpline').innerText = hospitalInfo.helpline;
        document.getElementById('emg-badge').innerText = `🚑 Emergency: ${hospitalInfo.emergency_number}`;
        document.getElementById('footer-emg').innerText = hospitalInfo.emergency_number;
        
        // Status indicator
        providerStatus.innerText = hospitalInfo.provider;
        providerStatus.className = `status-indicator ${hospitalInfo.is_demo ? 'demo' : 'connected'}`;
        
        // Render initial UI elements
        renderFaqs('all');
        setupSuggestedChips();
        
        // Add Welcome Message
        const welcomeText = `👋 Hello! I'm **${hospitalInfo.bot_name}**, your assistant at **${hospitalInfo.hospital_name}**.\n\n` +
                            `I can help you with appointments, OPD & visiting timings, departments, services, and emergency info.\n\n` +
                            `*Note: I can't give medical advice — for that, I'll help you book with a doctor.*`;
        
        appendMessage('assistant', welcomeText);
        
    } catch (err) {
        console.error("Error loading initial data:", err);
        faqAccordion.innerHTML = '<div class="error-msg">⚠️ Failed to connect to server. Make sure server.py is running.</div>';
    }
}

// Render FAQs based on category & search query
function renderFaqs(category = 'all', query = '') {
    faqAccordion.innerHTML = '';
    
    // Filter FAQs
    const filtered = allFaqs.filter(faq => {
        // Category check
        let inCat = false;
        const keys = faq.keywords.join(' ');
        
        if (category === 'all') {
            inCat = true;
        } else if (category === 'appointments') {
            inCat = keys.includes('appointment') || keys.includes('book');
        } else if (category === 'timings') {
            inCat = keys.includes('opd') || keys.includes('time') || keys.includes('visit');
        } else if (category === 'services') {
            inCat = keys.includes('pharmacy') || keys.includes('lab') || keys.includes('test') || keys.includes('scan');
        } else if (category === 'billing') {
            inCat = keys.includes('billing') || keys.includes('insurance') || keys.includes('charges');
        }
        
        // Search query check
        let matchesQuery = true;
        if (query) {
            const q = query.toLowerCase();
            matchesQuery = faq.title.toLowerCase().includes(q) || faq.answer.toLowerCase().includes(q);
        }
        
        return inCat && matchesQuery;
    });
    
    if (filtered.length === 0) {
        faqAccordion.innerHTML = '<div class="loading-placeholder">No matches found. Try asking the chatbot directly!</div>';
        return;
    }
    
    filtered.forEach((faq, index) => {
        const item = document.createElement('div');
        item.className = 'faq-item';
        
        const trigger = document.createElement('div');
        trigger.className = 'faq-trigger';
        trigger.innerHTML = `<h3>${faq.title}</h3><span class="faq-icon">▼</span>`;
        
        const content = document.createElement('div');
        content.className = 'faq-content';
        
        // Make body FAQ content
        let formattedAnswer = formatMarkdown(faq.answer);
        content.innerHTML = `
            <div>${formattedAnswer}</div>
            <button class="faq-action-btn" onclick="sendFaqQuestion('${faq.title}')">
                💬 Ask Assistant About This
            </button>
        `;
        
        trigger.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');
            // Close all items
            document.querySelectorAll('.faq-item').forEach(el => el.classList.remove('open'));
            
            if (!isOpen) {
                item.classList.add('open');
            }
        });
        
        item.appendChild(trigger);
        item.appendChild(content);
        faqAccordion.appendChild(item);
    });
}

// Setup Chips
function setupSuggestedChips() {
    const chips = [
        "How do I book an appointment?",
        "What are the OPD timings?",
        "Which departments are available?",
        "Emergency helpline?"
    ];
    
    chipsWrapper.innerHTML = '';
    chips.forEach(text => {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.innerText = text;
        chip.addEventListener('click', () => {
            sendUserMessage(text);
        });
        chipsWrapper.appendChild(chip);
    });
}

// Message Sending logic
function appendMessage(role, content) {
    const row = document.createElement('div');
    row.className = `msg-row ${role === 'user' ? 'user' : 'bot'}`;
    
    const avatar = document.createElement('div');
    avatar.className = `msg-avatar ${role === 'user' ? 'user' : 'bot'}`;
    avatar.innerText = role === 'user' ? '🧑' : '🩺';
    
    const bubble = document.createElement('div');
    bubble.className = `bubble ${role === 'user' ? 'user-bubble' : 'bot-bubble'}`;
    
    if (role === 'user') {
        bubble.innerText = content;
    } else {
        bubble.innerHTML = formatMarkdown(content);
    }
    
    row.appendChild(avatar);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Save to history
    chatHistory.push({ role, content });
}

// Show typing indicator
let typingIndicator = null;
function showTyping() {
    if (typingIndicator) return;
    
    const row = document.createElement('div');
    row.className = 'msg-row bot';
    
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar bot';
    avatar.innerText = '🩺';
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble bot-bubble';
    bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    
    row.appendChild(avatar);
    row.appendChild(bubble);
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    typingIndicator = row;
}

function removeTyping() {
    if (typingIndicator) {
        typingIndicator.remove();
        typingIndicator = null;
    }
}

// Main Send Action
async function sendUserMessage(text) {
    if (!text.trim()) return;
    
    appendMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendButton.disabled = true;
    
    showTyping();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ history: chatHistory })
        });
        
        const data = await response.json();
        removeTyping();
        
        if (data.reply) {
            appendMessage('assistant', data.reply);
        } else {
            appendMessage('assistant', "⚠️ Sorry, I encountered an issue handling that query.");
        }
    } catch (err) {
        removeTyping();
        appendMessage('assistant', "⚠️ Network connection lost. Please verify that the Flask server is running.");
    }
}

// Trigger sending from FAQ item
window.sendFaqQuestion = function(title) {
    sendUserMessage(`Tell me more about: ${title}`);
};

// Event Listeners
chatInput.addEventListener('input', () => {
    sendButton.disabled = !chatInput.value.trim();
    chatInput.style.height = 'auto';
    chatInput.style.height = (chatInput.scrollHeight) + 'px';
});

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const text = chatInput.value;
        if (text.trim()) {
            sendUserMessage(text);
        }
    }
});

sendButton.addEventListener('click', () => {
    const text = chatInput.value;
    if (text.trim()) {
        sendUserMessage(text);
    }
});

btnClearChat.addEventListener('click', () => {
    chatMessages.innerHTML = '';
    chatHistory = [];
    const welcomeText = `👋 Hello! I'm **${hospitalInfo.bot_name}**, your assistant at **${hospitalInfo.hospital_name}**.\n\n` +
                        `I can help you with appointments, OPD & visiting timings, departments, services, and emergency info.`;
    appendMessage('assistant', welcomeText);
});

// Category Tab Event Listeners
faqCategories.addEventListener('click', (e) => {
    if (e.target.classList.contains('category-tab')) {
        document.querySelectorAll('.category-tab').forEach(tab => tab.classList.remove('active'));
        e.target.classList.add('active');
        
        const cat = e.target.dataset.category;
        renderFaqs(cat, faqSearch.value);
    }
});

// Search functionality
faqSearch.addEventListener('input', (e) => {
    const query = e.target.value;
    clearSearchBtn.style.display = query ? 'block' : 'none';
    
    const activeTab = document.querySelector('.category-tab.active');
    const cat = activeTab ? activeTab.dataset.category : 'all';
    
    renderFaqs(cat, query);
});

clearSearchBtn.addEventListener('click', () => {
    faqSearch.value = '';
    clearSearchBtn.style.display = 'none';
    
    const activeTab = document.querySelector('.category-tab.active');
    const cat = activeTab ? activeTab.dataset.category : 'all';
    
    renderFaqs(cat, '');
});

// Init on load
document.addEventListener('DOMContentLoaded', init);
