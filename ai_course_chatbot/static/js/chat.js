// Chat application JavaScript

// DOM elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const sendButton = document.getElementById('send-button');
const showSourcesCheckbox = document.getElementById('show-sources');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

// State
let isWaitingForResponse = false;

const clearHistoryBtn = document.getElementById('clear-history-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    setupAutoResize();
    setupFormSubmit();
    loadChatHistory();
    clearHistoryBtn.addEventListener('click', clearChatHistory);
});

// Check chatbot status
async function checkStatus() {
    try {
        const response = await fetch('/chat/status');
        const data = await response.json();
        
        if (data.status === 'ready') {
            statusIndicator.className = 'status-ready';
            statusText.textContent = 'Ready';
        } else if (data.status === 'not_ready') {
            statusIndicator.className = 'status-not-ready';
            statusText.textContent = 'Not Ready - Upload documents first';
            showError(data.message);
        } else {
            statusIndicator.className = 'status-checking';
            statusText.textContent = 'Checking...';
        }
    } catch (error) {
        statusIndicator.className = 'status-not-ready';
        statusText.textContent = 'Connection Error';
        console.error('Error checking status:', error);
    }
}

// Auto-resize textarea
function setupAutoResize() {
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });
}

// Setup form submission
function setupFormSubmit() {
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await sendMessage();
    });

    // Allow Enter to send, Shift+Enter for new line
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

// Send message to chatbot
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isWaitingForResponse) {
        return;
    }

    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Disable input while waiting
    isWaitingForResponse = true;
    sendButton.disabled = true;
    userInput.disabled = true;

    // Create bot message container for streaming
    const botMessageDiv = createEmptyBotMessage();
    const contentEl = botMessageDiv.querySelector('.message-content');
    let fullText = '';

    try {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                show_sources: showSourcesCheckbox.checked
            })
        });

        if (!response.ok) {
            throw new Error('Stream request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') {
                        break;
                    }
                    if (data.startsWith('[ERROR]')) {
                        throw new Error(data);
                    }
                    fullText += data;
                    contentEl.textContent = fullText;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
        }

        // Format final text with paragraphs and sources
        formatBotMessage(contentEl, fullText);

    } catch (streamError) {
        console.warn('Streaming failed, falling back to standard endpoint:', streamError);
        // Fallback to non-streaming endpoint
        try {
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    show_sources: showSourcesCheckbox.checked
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get response');
            }

            const data = await response.json();
            formatBotMessage(contentEl, data.response, data.sources);

        } catch (fallbackError) {
            contentEl.textContent = 'Sorry, I encountered an error processing your request. Please try again.';
            showError(fallbackError.message);
        }
    } finally {
        isWaitingForResponse = false;
        sendButton.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }
}

// Create an empty bot message bubble for streaming
function createEmptyBotMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// Format bot message with paragraphs and optional sources
function formatBotMessage(contentEl, text, sources) {
    contentEl.innerHTML = '';

    // Split sources from text if embedded
    let responseText = text;
    let parsedSources = sources || [];

    if (!sources && text.includes('\n\nSources:')) {
        const parts = text.split('\n\nSources:');
        responseText = parts[0];
        if (parts.length > 1) {
            parsedSources = parts[1].trim().split('\n').filter(s => s.trim());
        }
    }

    // Add paragraphs
    const paragraphs = responseText.split('\n\n').filter(p => p.trim());
    paragraphs.forEach(para => {
        const p = document.createElement('p');
        p.textContent = para;
        contentEl.appendChild(p);
    });

    // Add sources
    if (parsedSources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.textContent = 'Sources:';
        sourcesDiv.appendChild(sourcesTitle);

        const sourcesList = document.createElement('ul');
        parsedSources.forEach(source => {
            const li = document.createElement('li');
            li.textContent = source;
            sourcesList.appendChild(li);
        });
        sourcesDiv.appendChild(sourcesList);
        contentEl.appendChild(sourcesDiv);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add message to chat
function addMessage(text, sender, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Format message text (support for paragraphs)
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    paragraphs.forEach(para => {
        const p = document.createElement('p');
        p.textContent = para;
        content.appendChild(p);
    });

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        
        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.textContent = 'Sources:';
        sourcesDiv.appendChild(sourcesTitle);
        
        const sourcesList = document.createElement('ul');
        sources.forEach(source => {
            const li = document.createElement('li');
            li.textContent = source;
            sourcesList.appendChild(li);
        });
        sourcesDiv.appendChild(sourcesList);
        content.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    
    content.appendChild(typingDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// ── Chat history ──────────────────────────────────────────────────────

// Load saved chat history from the server
async function loadChatHistory() {
    try {
        const response = await fetch('/chat/history');
        if (!response.ok) return;
        const data = await response.json();
        if (!data.entries || data.entries.length === 0) return;

        for (const entry of data.entries) {
            addMessage(entry.user_message, 'user');
            addMessage(entry.bot_response, 'bot', entry.sources || []);
        }
    } catch (err) {
        console.warn('Could not load chat history:', err);
    }
}

// Clear saved history on server and in the UI
async function clearChatHistory() {
    try {
        const response = await fetch('/chat/history', { method: 'DELETE' });
        if (!response.ok) {
            throw new Error(`Failed to clear history: ${response.status}`);
        }

        // Remove all messages except the welcome message only after server success.
        const messages = chatMessages.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(m => m.remove());
    } catch (err) {
        console.warn('Could not clear history on server:', err);
        showError('Could not clear chat history. Please try again.');
    }
}

// Show error message
function showError(message) {
    // Check if error already exists
    let errorDiv = document.querySelector('.error-message');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        chatMessages.parentElement.insertBefore(errorDiv, chatMessages);
    }
    
    errorDiv.textContent = message;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
}
