#!/usr/bin/env python3
"""
Script para testar a instalação das dependências
"""
import sys

def test_imports():
    """Testa se todas as dependências estão instaladas corretamente"""
    print("Testando importações das dependências...")
    
    try:
        import requests
        print("✓ requests - OK")
    except ImportError as e:
        print(f"✗ requests - ERRO: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4 - OK")
    except ImportError as e:
        print(f"✗ beautifulsoup4 - ERRO: {e}")
        return False
    
    try:
        import selenium
        from selenium import webdriver
        print("✓ selenium - OK")
    except ImportError as e:
        print(f"✗ selenium - ERRO: {e}")
        return False
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ webdriver-manager - OK")
    except ImportError as e:
        print(f"✗ webdriver-manager - ERRO: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv - OK")
    except ImportError as e:
        print(f"✗ python-dotenv - ERRO: {e}")
        return False
    
    try:
        import pandas
        print("✓ pandas - OK")
    except ImportError as e:
        print(f"✗ pandas - ERRO: {e}")
        return False
    
    try:
        import schedule
        print("✓ schedule - OK")
    except ImportError as e:
        print(f"✗ schedule - ERRO: {e}")
        return False
    
    return True

def test_selenium_webdriver():
    """Testa se o Selenium consegue inicializar o WebDriver"""
    print("\nTestando Selenium WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Configurações do Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executa sem interface gráfica
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Instala e configura o ChromeDriver automaticamente
        service = Service(ChromeDriverManager().install())
        
        # Cria instância do driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Testa uma requisição simples
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        
        print(f"✓ Selenium WebDriver - OK (Título da página: {title})")
        return True
        
    except Exception as e:
        print(f"✗ Selenium WebDriver - ERRO: {e}")
        print("Verifique se o Chrome/Chromium está instalado no sistema")
        return False

def test_database():
    """Testa se consegue criar o banco de dados"""
    print("\nTestando criação do banco de dados...")
    
    try:
        import sqlite3
        import os
        
        # Cria diretório de dados se não existir
        os.makedirs("data", exist_ok=True)
        
        # Testa conexão com SQLite
        conn = sqlite3.connect("data/test.db")
        cursor = conn.cursor()
        
        # Cria tabela de teste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insere dados de teste
        cursor.execute("INSERT INTO test (name) VALUES (?)", ("teste",))
        
        # Verifica se dados foram inseridos
        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        # Remove arquivo de teste
        os.remove("data/test.db")
        
        print(f"✓ SQLite Database - OK (Inseriu e consultou {count} registro)")
        return True
        
    except Exception as e:
        print(f"✗ SQLite Database - ERRO: {e}")
        return False

def main():
    """Função principal do teste"""
    print("="*60)
    print("TESTE DE INSTALAÇÃO - F1 WEB SCRAPING PROJECT")
    print("="*60)
    
    # Testa importações
    imports_ok = test_imports()
    
    # Testa Selenium
    selenium_ok = test_selenium_webdriver()
    
    # Testa banco de dados
    database_ok = test_database()
    
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    print("="*60)
    
    if imports_ok and selenium_ok and database_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("O projeto está pronto para ser executado.")
        print("\nPara iniciar o scraping:")
        print("python main.py all")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("Verifique os erros acima e instale as dependências necessárias.")
        sys.exit(1)

if __name__ == "__main__":
    main()
