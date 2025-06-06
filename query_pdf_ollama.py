import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from llama_index.core import Document, VectorStoreIndex
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.settings import Settings
import warnings
import sys
import io
import contextlib
from llama_index.core.node_parser import SentenceSplitter


# Configuração do OCR em português
OCR_LANG = 'por'

# Caminhos para as pastas
PDF_DIR = "pdfs"
HTML_DIR = "html_texts"

warnings.filterwarnings("ignore")

@contextlib.contextmanager
def suprimir_stderr():
    stderr_original = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = stderr_original

# Extrai texto de PDFs digitalizados com OCR
def extrair_texto_ocr(caminho_pdf):
    paginas = convert_from_path(caminho_pdf)
    texto_total = ""
    for i, imagem in enumerate(paginas):
        texto = pytesseract.image_to_string(imagem, lang=OCR_LANG)
        texto_total += texto + "\n"
    return texto_total



def carregar_documentos():
    documentos = []

    os.makedirs("pdf_texts_cache", exist_ok=True)

    # 1. PDFs
    for nome_arquivo in os.listdir(PDF_DIR):
        if nome_arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)
            nome_txt = nome_arquivo.replace(".pdf", ".txt")
            caminho_txt = os.path.join("pdf_texts_cache", nome_txt)

            # Usa cache se já existir
            if os.path.exists(caminho_txt):
                print(f"[CACHE] A carregar texto já extraído de: {nome_arquivo}")
                with open(caminho_txt, "r", encoding="utf-8") as f:
                    texto_total = f.read()
                documentos.append(Document(text=texto_total))
                continue

            texto_total = ""

            # Tenta leitura com pdfplumber
            try:
                with suprimir_stderr():
                    with pdfplumber.open(caminho_pdf) as pdf:
                        texto_total = "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                print(f"[ERRO] pdfplumber falhou com {nome_arquivo}: {e}")
                texto_total = ""

            # Se falhar, tenta OCR
            if not texto_total.strip():
                try:
                    print(f"[OCR] A extrair texto via OCR de: {nome_arquivo}")
                    paginas = convert_from_path(caminho_pdf)
                    for imagem in paginas:
                        texto_total += pytesseract.image_to_string(imagem, lang=OCR_LANG) + "\n"
                except Exception as e:
                    print(f"[ERRO] OCR falhou com {nome_arquivo}: {e}")
                    continue  # Ignora este ficheiro

            # Guarda cache
            with open(caminho_txt, "w", encoding="utf-8") as f:
                f.write(texto_total)

            documentos.append(Document(text=texto_total))

    # 2. HTMLs
    for nome_arquivo in os.listdir(HTML_DIR):
        if nome_arquivo.endswith(".txt"):
            caminho_txt = os.path.join(HTML_DIR, nome_arquivo)
            try:
                with open(caminho_txt, "r", encoding="utf-8") as f:
                    texto = f.read()
                    documentos.append(Document(text=texto))
            except Exception as e:
                print(f"[ERRO] Falha ao ler HTML {nome_arquivo}: {e}")

    return documentos

def verificar_chunks_indexados(index, termo_busca, top_k=5):
    print(f"\n🔍 A verificar os chunks mais semelhantes a: '{termo_busca}'\n")
    
    results = index.similarity_top_k(termo_busca, k=top_k)
    
    for i, node in enumerate(results, 1):
        print(f"[{i}] Chunk (score: {node.score:.4f}):\n{node.text}\n{'-'*60}")


# Função principal
def main():
    print("[1] A carregar documentos PDF (com suporte a OCR)...")
    documentos = carregar_documentos()

    if not documentos:
        print("❌ Nenhum PDF encontrado na pasta:", PDF_DIR)
        return

    print("[2] A configurar embeddings locais com Ollama (modelo: nomic-embed-text)...")
    from llama_index.embeddings.ollama import OllamaEmbedding
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

    print("[3] A indexar documentos com LlamaIndex...")
    from llama_index.core.node_parser import SentenceSplitter
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    index = VectorStoreIndex.from_documents(documentos, transformations=[parser])

    print("[4] A preparar o modelo Ollama (Mistral)...")
    llm = Ollama(model="mistral")
    query_engine = index.as_query_engine(llm=llm)

    print("\n[5] Pronto para perguntas. Escreve 'sair' para terminar.")
    while True:
        pergunta = input("\nA tua pergunta: ")
        if pergunta.lower() in ("sair", "exit", "quit"):
            break
        prompt = (
            "Assumes o papel de um assistente virtual oficial do Instituto Politécnico de Viana do Castelo (IPVC), especializado em prestar apoio com base exclusivamente nos documentos fornecidos pelo utilizador.\n\n"
            "Consulta e responde apenas com base na informação extraída dos documentos disponibilizados (como calendários, provas modelo, regulamentos, entre outros). Não deves inventar informação nem responder com base em conhecimentos externos ou generalizações.\n\n"
            "Se a pergunta estiver fora do âmbito da documentação carregada, responde claramente que não tens essa informação.\n\n"
            "Responde sempre em português de Portugal, de forma clara, objetiva e informativa.\n\n"
            f"Pergunta: {pergunta}"
        )

        resposta = query_engine.query(prompt)
        resposta_texto = str(resposta)
        if "IPVC" not in resposta_texto and "Viana do Castelo" not in resposta_texto:
            resposta_texto = "❌ Informação fora do âmbito do IPVC. Por favor, consulte apenas fontes oficiais do IPVC."

        print("\nResposta:\n", resposta_texto)
        
if __name__ == "__main__":
    main()
