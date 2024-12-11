import sys
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time
import urllib3

# Suprimindo o aviso InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_emails_from_url(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    pattern = r'[\w\.-]+@[\w\.-]+|\[at\]'
    emails = re.findall(pattern, soup.get_text())

    emails = [email.replace('[at]', '@') for email in emails if '@' in email or '[at]' in email]
    emails = [email.replace('[dot]', '.') for email in emails if '.' in email or '[dot]' in email]

    return emails

def cleanup_email(email):
    valid_domains = ['.com', '.com.br', '.gov.br', '.br']
    for domain in valid_domains:
        if email.endswith(domain):
            return email
    # Remove qualquer coisa após os domínios válidos
    for domain in valid_domains:
        if domain in email:
            return email[:email.rfind(domain) + len(domain)]
    return email

def crawl_website(url, visited_pages, max_pages=100, depth=0):
    if len(visited_pages) >= max_pages or depth > 2:  # Limitando a profundidade de rastreamento
        return

    if url in visited_pages:
        return

    visited_pages.add(url)

    print(f"Buscando: {url}")

    emails = extract_emails_from_url(url)
    cleaned_emails = [cleanup_email(email) for email in emails]
    if cleaned_emails:
        filename = f"{urlparse(url).netloc}_emails.txt".replace('/', '_').replace(':', '_')
        save_emails_to_txt(cleaned_emails, filename)

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        response.raise_for_status()
    except requests.RequestException:
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    for link in soup.find_all('a', href=True):
        absolute_link = urljoin(url, link['href'])
        parsed_link = urlparse(absolute_link)
        
        if parsed_link.netloc.endswith(urlparse(url).netloc):
            crawl_website(absolute_link, visited_pages, max_pages, depth + 1)
            
        time.sleep(1)  # Espera de 1 segundo entre as requisições

def save_emails_to_txt(emails, filename):
    # Lendo emails existentes no arquivo
    existing_emails = set()
    try:
        with open(filename, 'r') as file:
            for line in file:
                existing_emails.update(line.strip().split(','))
    except FileNotFoundError:
        pass

    # Adicionando novos emails ao arquivo
    with open(filename, 'a') as file:
        for email in emails:
            if email not in existing_emails:
                file.write(f"{email},\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python EmailColetor.py <URL>")
        sys.exit(1)

    start_url = sys.argv[1]  # URL inicial fornecida como argumento
    visited_pages = set()

    crawl_website(start_url, visited_pages)

    print(f"{len(visited_pages)} páginas foram visitadas.")
