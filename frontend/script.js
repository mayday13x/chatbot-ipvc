document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatWindow = document.getElementById('chat-window');

    const API_URL = 'http://localhost:5000/chat';

    let loadingMessageElement = null;

    // Função para adicionar mensagens ao chat com avatares
    function addMessage(message, sender) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container', sender);

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar', sender);
        if (sender === 'user') {
            avatar.textContent = 'Tu';
        } else {
            avatar.innerHTML = '<svg width="24" height="24" viewBox="0 0 40 20" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="0" y="15" font-family="Arial" font-size="16" fill="#F7931E" font-weight="bold">IPVC</text></svg>';
            avatar.style.backgroundColor = '#1A1A1A';
            avatar.style.color = '#F7931E';
        }

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content', sender);
        messageContent.textContent = message;

        if (sender === 'user') {
            messageContainer.appendChild(messageContent);
            messageContainer.appendChild(avatar);
        } else {
            messageContainer.appendChild(avatar);
            messageContainer.appendChild(messageContent);
        }

        chatWindow.appendChild(messageContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Função melhorada para mostrar o indicador de carregamento
    function showLoadingIndicator() {
        // Remove qualquer loading anterior (precaução)
        hideLoadingIndicator();
        
        loadingMessageElement = document.createElement('div');
        loadingMessageElement.classList.add('message-container', 'bot', 'loading-message');

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar', 'bot');
        avatar.innerHTML = '<svg width="24" height="24" viewBox="0 0 40 20" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="0" y="15" font-family="Arial" font-size="16" fill="#F7931E" font-weight="bold">IPVC</text></svg>';
        avatar.style.backgroundColor = '#1A1A1A';
        avatar.style.color = '#F7931E';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content', 'bot', 'loading-content');
        
        // Criar os pontos de loading
        const dotsContainer = document.createElement('div');
        dotsContainer.classList.add('loading-dots');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.classList.add('loading-dot');
            dotsContainer.appendChild(dot);
        }
        
        messageContent.appendChild(dotsContainer);
        loadingMessageElement.appendChild(avatar);
        loadingMessageElement.appendChild(messageContent);

        chatWindow.appendChild(loadingMessageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Desabilitar inputs durante o loading
        userInput.disabled = true;
        sendButton.disabled = true;
        sendButton.style.opacity = '0.5';
    }

    // Função para esconder o indicador de carregamento
    function hideLoadingIndicator() {
        if (loadingMessageElement && loadingMessageElement.parentNode) {
            chatWindow.removeChild(loadingMessageElement);
            loadingMessageElement = null;
        }
        
        // Reabilitar inputs
        userInput.disabled = false;
        sendButton.disabled = false;
        sendButton.style.opacity = '1';
        userInput.focus();
    }

    // Função para auto-redimensionar o textarea
    function autoResizeTextarea() {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    }

    // Função para simular digitação (opcional - efeito extra)
    function typeMessage(message, element, speed = 30) {
        return new Promise((resolve) => {
            element.textContent = '';
            let i = 0;
            const timer = setInterval(() => {
                if (i < message.length) {
                    element.textContent += message.charAt(i);
                    i++;
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                } else {
                    clearInterval(timer);
                    resolve();
                }
            }, speed);
        });
    }

    async function sendMessage() {
        const pergunta = userInput.value.trim();
        if (pergunta === '' || userInput.disabled) return;

        // Adicionar mensagem do usuário
        addMessage(pergunta, 'user');
        userInput.value = '';
        autoResizeTextarea();
        
        // Mostrar loading
        showLoadingIndicator();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pergunta: pergunta })
            });

            const data = await response.json();

            // Esconder loading antes de mostrar a resposta
            hideLoadingIndicator();

            if (response.ok) {
                // Adicionar pequeno delay para transição suave
                setTimeout(() => {
                    addMessage(data.resposta, 'bot');
                }, 100);
            } else {
                setTimeout(() => {
                    addMessage(`Erro: ${data.erro || 'Não foi possível obter resposta.'}`, 'bot');
                }, 100);
            }
        } catch (error) {
            console.error('Erro ao comunicar com a API:', error);
            hideLoadingIndicator();
            setTimeout(() => {
                addMessage('Erro: Não foi possível conectar ao servidor.', 'bot');
            }, 100);
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('input', autoResizeTextarea);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !userInput.disabled) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Mensagem de boas-vindas inicial
    addMessage("Olá! Sou o assistente do IPVC. Como posso ajudar-te hoje?", 'bot');
    autoResizeTextarea();
});