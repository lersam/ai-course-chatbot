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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    setupAutoResize();
    setupFormSubmit();
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

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        const response = await fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                show_sources: showSourcesCheckbox.checked
            })
        });

        // Remove typing indicator
        typingIndicator.remove();

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get response');
        }

        const data = await response.json();
        
        // Add bot response to chat
        addMessage(data.response, 'bot', data.sources);

    } catch (error) {
        typingIndicator.remove();
        console.error('Error sending message:', error);
        addMessage(
            'Sorry, I encountered an error processing your request. Please try again.',
            'bot'
        );
        showError(error.message);
    } finally {
        // Re-enable input
        isWaitingForResponse = false;
        sendButton.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }
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
