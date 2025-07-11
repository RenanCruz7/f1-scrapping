"""
Scraper base e configurações comuns
"""
import requests
import time
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class BaseScraper:
    """Classe base para todos os scrapers"""
    
    def __init__(self, base_url: str, delay: float = 1.0, timeout: int = 30):
        """
        Inicializa o scraper base
        
        Args:
            base_url: URL base para scraping
            delay: Delay entre requisições (segundos)
            timeout: Timeout para requisições (segundos)
        """
        self.base_url = base_url
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Headers padrão para parecer mais com um navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Faz requisição HTTP e retorna objeto BeautifulSoup
        
        Args:
            url: URL para fazer a requisição
            retries: Número de tentativas em caso de falha
            
        Returns:
            Objeto BeautifulSoup ou None se falhou
        """
        for attempt in range(retries):
            try:
                self.logger.info(f"Fazendo requisição para: {url} (tentativa {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Delay entre requisições para ser respeitoso
                time.sleep(self.delay)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.RequestException as e:
                self.logger.warning(f"Erro na requisição (tentativa {attempt + 1}): {e}")
                if attempt == retries - 1:
                    self.logger.error(f"Falha após {retries} tentativas para {url}")
                    return None
                time.sleep(2 ** attempt)  # Backoff exponencial
        
        return None
    
    def get_selenium_driver(self, headless: bool = True) -> webdriver.Chrome:
        """
        Cria e retorna um driver do Selenium Chrome
        
        Args:
            headless: Se deve executar em modo headless
            
        Returns:
            Instância do driver Chrome
        """
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={self.session.headers['User-Agent']}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return driver
    
    def safe_extract_text(self, element, default: str = "") -> str:
        """
        Extrai texto de um elemento de forma segura
        
        Args:
            element: Elemento BeautifulSoup
            default: Valor padrão se elemento for None
            
        Returns:
            Texto extraído ou valor padrão
        """
        if element:
            return element.get_text(strip=True)
        return default
    
    def safe_extract_attr(self, element, attr: str, default: str = "") -> str:
        """
        Extrai atributo de um elemento de forma segura
        
        Args:
            element: Elemento BeautifulSoup
            attr: Nome do atributo
            default: Valor padrão se elemento for None
            
        Returns:
            Valor do atributo ou valor padrão
        """
        if element and element.has_attr(attr):
            return element[attr]
        return default
    
    def clean_text(self, text: str) -> str:
        """
        Limpa e normaliza texto extraído
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo e normalizado
        """
        if not text:
            return ""
        
        # Remove espaços extras e quebras de linha
        cleaned = " ".join(text.split())
        
        # Remove caracteres especiais comuns
        cleaned = cleaned.replace("\\n", " ").replace("\\t", " ")
        
        return cleaned.strip()
    
    def parse_number(self, text: str) -> Optional[int]:
        """
        Extrai número de uma string
        
        Args:
            text: Texto contendo número
            
        Returns:
            Número extraído ou None se não encontrado
        """
        if not text:
            return None
        
        # Remove tudo que não for dígito
        digits = ''.join(filter(str.isdigit, text))
        
        try:
            return int(digits) if digits else None
        except ValueError:
            return None
