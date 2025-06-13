from flask import Flask, request, jsonify
from flask_cors import CORS
from query_pdf_ollama import get_chatbot_response, initialize_chatbot

app = Flask(__name__)
CORS(app) # Permite que o frontend (em um domínio diferente) acesse esta API

# Inicializa o chatbot quando a aplicação Flask é iniciada
with app.app_context():
    system_prompt = """ És um assistente especializado do Instituto Politécnico de Viana do Castelo. 
            A tua função é analisar TODOS os documentos disponíveis e responder a perguntas de forma completa e precisa.
            IMPORTANTE:
            - SEMPRE procura a informação em TODOS os documentos disponíveis
            - NUNCA digas que a informação não está presente sem teres verificado TODOS os documentos
            - Se encontrares a informação em qualquer documento, utiliza-a imediatamente
            - Se não encontrares a informação exata, procura informações relacionadas ou contextuais
            - Responde sempre em português de Portugal
            - Sê proativo e detalhado nas respostas
            - Se a informação estiver presente, NUNCA digas que não a encontraste
            - Se a pergunta não estiver relacionada com o IPVC, responde de forma simpática que só podes responder a questões relacionadas com o IPVC
            - Explica sempre de forma educada e simpática quando uma pergunta está fora do teu âmbito de conhecimento
            - Tenta não mencione os nomes dos documentos ou fontes nas suas respostas"""
    initialize_chatbot()

@app.route('/', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    pergunta = data.get('pergunta')

    if not pergunta:
        return jsonify({'erro': 'Pergunta não fornecida'}), 400

    resposta = get_chatbot_response(pergunta)
    return jsonify({'resposta': resposta})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 