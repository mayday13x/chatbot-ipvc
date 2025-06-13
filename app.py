from flask import Flask, request, jsonify
from flask_cors import CORS
from query_pdf_ollama import get_chatbot_response, initialize_chatbot

app = Flask(__name__)
CORS(app) # Permite que o frontend (em um domínio diferente) acesse esta API

# Inicializa o chatbot quando a aplicação Flask é iniciada
with app.app_context():
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