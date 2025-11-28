document.addEventListener('DOMContentLoaded', () => {
    const aiChatBtn = document.getElementById('ai-chat-btn');
    const aiChatWidget = document.getElementById('ai-chat-widget');
    const aiChatMessages = document.getElementById('ai-chat-messages');
    const aiChatActions = document.getElementById('ai-chat-actions');
    const aiChatInput = document.getElementById('ai-chat-input');

    let chatVisible = false;

    aiChatBtn.addEventListener('click', () => {
        chatVisible = !chatVisible;
        aiChatWidget.style.display = chatVisible ? 'flex' : 'none';
        if (chatVisible) {
            sendMessage('hello');
        }
    });

    aiChatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage(aiChatInput.value);
            aiChatInput.value = '';
        }
    });

    function sendMessage(message) {
        addMessage(message, 'user');
        fetch('/api/v1/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
        .then(response => response.json())
        .then(data => {
            addMessage(data.data.response, 'ai');
            displayActions(data.data.actions);
        });
    }

    function addMessage(message, sender) {
        const messageElement = document.createElement('p');
        messageElement.innerHTML = `<strong>${sender === 'user' ? 'You' : 'AtroZ AI'}:</strong> ${message}`;
        aiChatMessages.appendChild(messageElement);
        aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
    }

    function displayActions(actions) {
        aiChatActions.innerHTML = '';
        actions.forEach(action => {
            const actionButton = document.createElement('button');
            actionButton.innerText = action;
            actionButton.addEventListener('click', () => {
                sendMessage(action);
            });
            aiChatActions.appendChild(actionButton);
        });
    }
});
