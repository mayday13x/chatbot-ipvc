document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatWindow = document.getElementById('chat-window');

    const API_URL = 'http://localhost:5000/chat';

    let loadingMessageElement = null; // Variável para armazenar a mensagem de carregamento

    // Função para adicionar mensagens ao chat com avatares
    function addMessage(message, sender) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container', sender);

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar', sender);
        if (sender === 'user') {
            avatar.textContent = 'Tu';
        } else {
            // SVG para o avatar do bot com texto "IPVC"
            avatar.innerHTML = '<svg width="24" height="24" viewBox="0 0 40 20" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="0" y="15" font-family="Arial" font-size="16" fill="#F7931E" font-weight="bold">IPVC</text></svg>';
            avatar.style.backgroundColor = '#1A1A1A'; // Fundo escuro para o ícone do bot
            avatar.style.color = '#F7931E'; // Cor do texto
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
        chatWindow.scrollTop = chatWindow.scrollHeight; // Rolar para a última mensagem
    }

    // Função para mostrar o indicador de carregamento
    function showLoadingIndicator() {
        loadingMessageElement = document.createElement('div');
        loadingMessageElement.classList.add('message-container', 'bot', 'loading');

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar', 'bot');
        // SVG para o avatar do bot com texto "IPVC" para o loading
        avatar.innerHTML = '<svg width="24" height="24" viewBox="0 0 40 20" fill="none" xmlns="http://www.w3.org/2000/svg"><text x="0" y="15" font-family="Arial" font-size="16" fill="#F7931E" font-weight="bold">IPVC</text></svg>';
        avatar.style.backgroundColor = '#1A1A1A';
        avatar.style.color = '#F7931E';

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content', 'bot');
        messageContent.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

        loadingMessageElement.appendChild(avatar);
        loadingMessageElement.appendChild(messageContent);

        chatWindow.appendChild(loadingMessageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        userInput.disabled = true;
        sendButton.disabled = true;
    }

    // Função para esconder o indicador de carregamento
    function hideLoadingIndicator() {
        if (loadingMessageElement) {
            chatWindow.removeChild(loadingMessageElement);
            loadingMessageElement = null;
        }
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }

    // Função para auto-redimensionar o textarea
    function autoResizeTextarea() {
        userInput.style.height = 'auto'; // Reset para calcular a altura real
        userInput.style.height = userInput.scrollHeight + 'px';
    }

    async function sendMessage() {
        const pergunta = userInput.value.trim();
        if (pergunta === '') return;

        addMessage(pergunta, 'user');
        userInput.value = '';
        autoResizeTextarea(); // Redimensionar de volta para o tamanho inicial
        showLoadingIndicator(); // Mostrar o indicador de carregamento

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pergunta: pergunta })
            });

            const data = await response.json();

            if (response.ok) {
                addMessage(data.resposta, 'bot');
            } else {
                addMessage(`Erro: ${data.erro || 'Não foi possível obter resposta.'}`, 'bot');
            }
        } catch (error) {
            console.error('Erro ao comunicar com a API:', error);
            addMessage('Erro: Não foi possível conectar ao servidor.', 'bot');
        } finally {
            hideLoadingIndicator(); // Esconder o indicador de carregamento e reativar inputs
        }
    }

    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('input', autoResizeTextarea); // Auto-redimensionar ao digitar
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !userInput.disabled) { // Enter para enviar, Shift+Enter para nova linha
            e.preventDefault(); // Previne nova linha no textarea
            sendMessage();
        }
    });

    // Mensagem de boas-vindas inicial
    addMessage("Olá! Sou o assistente do IPVC. Como posso ajudar-te hoje?", 'bot');
    autoResizeTextarea(); // Ajustar tamanho inicial do textarea
}); 