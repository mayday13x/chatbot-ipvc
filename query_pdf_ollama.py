import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SentenceSplitter
import warnings
import sys
import io
import contextlib

OCR_LANG = 'por'  # OCR em português
PDF_DIR = "pdfs"
CACHE_DIR = "pdf_texts_cache"

warnings.filterwarnings("ignore")

@contextlib.contextmanager
def suprimir_stderr():
    stderr_original = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = stderr_original

def extrair_texto_pdf(caminho_pdf):
    texto_total = ""
    # Tenta com pdfplumber
    try:
        with suprimir_stderr():
            with pdfplumber.open(caminho_pdf) as pdf:
                texto_total = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        texto_total = ""

    # Se não extraiu texto, tenta OCR
    if not texto_total.strip():
        print(f"[OCR] Extrair texto via OCR: {os.path.basename(caminho_pdf)}")
        try:
            paginas = convert_from_path(caminho_pdf)
            for imagem in paginas:
                texto_total += pytesseract.image_to_string(imagem, lang=OCR_LANG) + "\n"
        except Exception as e:
            print(f"[ERRO] OCR falhou para {os.path.basename(caminho_pdf)}: {e}")
    return texto_total

def carregar_documentos():
    os.makedirs(CACHE_DIR, exist_ok=True)
    documentos = []

    for arquivo in os.listdir(PDF_DIR):
        if arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(PDF_DIR, arquivo)
            caminho_cache = os.path.join(CACHE_DIR, arquivo.replace(".pdf", ".txt"))

            if os.path.exists(caminho_cache):
                print(f"[CACHE] Carregando texto cacheado: {arquivo}")
                with open(caminho_cache, "r", encoding="utf-8") as f:
                    texto = f.read()
            else:
                texto = extrair_texto_pdf(caminho_pdf)
                with open(caminho_cache, "w", encoding="utf-8") as f:
                    f.write(texto)

            documentos.append(Document(text=texto, metadata={"fonte": arquivo}))

    return documentos

# Variáveis globais para o índice e o motor de consulta
_index = None
_query_engine = None

def initialize_chatbot():
    global _index, _query_engine
    if _index is None:
        print("[1] Carregando documentos PDF...")
        documentos = carregar_documentos()
        if not documentos:
            print("Nenhum documento PDF encontrado.")
            return None # Retorna None se não houver documentos para indicar falha na inicialização
        print(f"[INFO] {len(documentos)} documentos carregados.")

        print("[2] Configurando embeddings Ollama...")
        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

        print("[3] Criando índice LlamaIndex...")
        parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
        _index = VectorStoreIndex.from_documents(documentos, transformations=[parser])

        print("[4] Configurando modelo Ollama...")
        llm = Ollama(
            model="llama3:instruct", 
            temperature=0.1,
            system_prompt="""És um assistente especializado do Instituto Politécnico de Viana do Castelo. 
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
            - Explica sempre de forma educada e simpática quando uma pergunta está fora do teu âmbito de conhecimento"""
        )

        _query_engine = _index.as_query_engine(
            llm=llm,
            similarity_top_k=20,
            response_mode="tree_summarize"
        )
        print("[INFO] Chatbot inicializado e pronto.")
    return _query_engine

def get_chatbot_response(pergunta):
    query_engine = initialize_chatbot()
    if query_engine is None:
        return "Erro: O chatbot não foi inicializado. Nenhum documento PDF encontrado ou ocorreu um problema na configuração."

    pergunta_formatada = f"""Analisa TODOS os documentos disponíveis e responde em português: {pergunta}
    IMPORTANTE: 
    - Procura a informação em TODOS os documentos
    - Se encontrares a informação, responde imediatamente
    - Não digas que não encontraste a informação sem teres verificado todos os documentos
    - Sê detalhado e preciso na resposta
    - Se a pergunta não estiver relacionada com o IPVC, explica de forma simpática que só podes responder a questões do IPVC"""
    
    resposta = query_engine.query(pergunta_formatada)
    return str(resposta)

if __name__ == "__main__":
    # Este bloco só será executado se o script for executado diretamente
    # Mantenho para fins de teste manual
    initialize_chatbot()
    print("\n[5] Pronto para perguntas (digite 'sair' para encerrar).")
    while True:
        pergunta = input("\nSua pergunta: ")
        if pergunta.lower() in ("sair", "exit", "quit"):
            break
        resposta = get_chatbot_response(pergunta)
        print("\n📝 Resposta:")
        print(resposta)