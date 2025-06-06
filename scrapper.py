import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract

# Configurações
START_URL = 'https://www.ipvc.pt/estudar/candidato-ipvc/mestrados/'
PDF_FOLDER = 'pdfs'
TEXT_FOLDER = 'pdf_texts'
HTML_TEXT_FOLDER = 'html_texts'
OCR_LANG = 'por'
MAX_DEPTH = 1  # Podes aumentar para seguir links mais internos

visited = set()
pdf_links = set()

def is_internal(base_url, target_url):
    return urlparse(base_url).netloc in urlparse(target_url).netloc

def salvar_texto(nome, conteudo, pasta):
    os.makedirs(pasta, exist_ok=True)
    path = os.path.join(pasta, nome)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(conteudo)

def scrape_site(url, base_url, current_depth=0):
    if current_depth > MAX_DEPTH or url in visited:
        return
    visited.add(url)

    try:
        print(f"{'  ' * current_depth}🧭 [Nível {current_depth}] Visitando: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (bot)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Salvar texto da página HTML
        texto_html = soup.get_text(separator="\n", strip=True)
        nome_arquivo = urlparse(url).path.strip('/').replace('/', '_') or 'index'
        salvar_texto(nome_arquivo + ".txt", texto_html, HTML_TEXT_FOLDER)

        # Extrair todos os links
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])

            if full_url.endswith('.pdf'):
                pdf_links.add(full_url)
            elif is_internal(base_url, full_url):
                scrape_site(full_url, base_url, current_depth + 1)

    except Exception as e:
        print(f"{'  ' * current_depth}❌ Erro ao aceder {url}: {e}")
    time.sleep(0.5)

def download_pdfs(pdf_urls, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for url in pdf_urls:
        try:
            filename = os.path.join(output_folder, os.path.basename(url))
            print(f"⬇️  Baixando {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (bot)'}
            r = requests.get(url, headers=headers)
            with open(filename, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print(f"Erro ao baixar {url}: {e}")

def extract_text_from_pdfs(pdf_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for pdf_file in os.listdir(pdf_folder):
        try:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            text_path = os.path.join(output_folder, pdf_file.replace('.pdf', '.txt'))

            print(f"📝 A extrair texto de {pdf_file}")
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()

            if not text.strip():
                print(f"🔍 [OCR] A extrair com OCR de {pdf_file}")
                imagens = convert_from_path(pdf_path)
                for imagem in imagens:
                    text += pytesseract.image_to_string(imagem, lang=OCR_LANG) + "\n"

            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)

        except Exception as e:
            print(f"Erro ao extrair texto de {pdf_file}: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando scraping do IPVC com suporte a HTML + PDFs + OCR...\n")

    # Etapa 1: Scraping do conteúdo das páginas e coleta de links de PDF
    scrape_site(START_URL, START_URL)

    # Etapa 2: Download dos PDFs encontrados
    print(f"\n📄 {len(pdf_links)} PDFs encontrados. Iniciando download...\n")
    download_pdfs(pdf_links, PDF_FOLDER)

    # Etapa 3: Extração de texto dos PDFs (com fallback para OCR)
    print(f"\n🧠 Iniciando extração de texto dos PDFs...\n")
    extract_text_from_pdfs(PDF_FOLDER, TEXT_FOLDER)

    print("\n✅ Tudo pronto! Textos HTML e PDFs extraídos com sucesso.")
