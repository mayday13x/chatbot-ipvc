import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.settings import Settings
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

def main():
    print("[1] Carregando documentos PDF...")
    documentos = carregar_documentos()
    if not documentos:
        print("Nenhum documento PDF encontrado.")
        return
    print(f"[INFO] {len(documentos)} documentos carregados.")

    print("[2] Configurando embeddings Ollama...")
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

    print("[3] Criando índice LlamaIndex...")
    parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
    index = VectorStoreIndex.from_documents(documentos, transformations=[parser])

    print("[4] Configurando modelo Ollama...")
    llm = Ollama(
        model="llama3:instruct", 
        temperature=0.1,
        system_prompt="Você é um assistente da faculdade do Instituto Politénico de Viana do Castelo que responde sempre em português portugal. Analise os documentos fornecidos e responda as perguntas de forma clara e detalhada em português."
    )

    query_engine = index.as_query_engine(
        llm=llm,
        similarity_top_k=10,
        response_mode="compact"
    )

    print("\n[5] Pronto para perguntas (digite 'sair' para encerrar).")
    while True:
        pergunta = input("\nSua pergunta: ")
        if pergunta.lower() in ("sair", "exit", "quit"):
            break

        # Adiciona instrução em português na pergunta
        pergunta_formatada = f"Responda em português: {pergunta}"
        resposta = query_engine.query(pergunta_formatada)
        print("\n📝 Resposta:")
        print(str(resposta))

if __name__ == "__main__":
    main()