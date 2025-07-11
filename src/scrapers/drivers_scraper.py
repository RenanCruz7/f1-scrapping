"""
Scraper para dados de pilotos de F1
"""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from . import BaseScraper
from ..models import Driver
from ..database import DatabaseManager


class DriversScraper(BaseScraper):
    """Scraper para coletar informações dos pilotos de F1"""
    
    def __init__(self):
        super().__init__("https://www.formula1.com")
        self.drivers_endpoint = "/en/drivers.html"
    
    def scrape_all_drivers(self, db_manager: DatabaseManager) -> List[Driver]:
        """
        Coleta informações de todos os pilotos atuais
        
        Args:
            db_manager: Instância do gerenciador do banco de dados
            
        Returns:
            Lista de objetos Driver
        """
        drivers = []
        url = urljoin(self.base_url, self.drivers_endpoint)
        
        soup = self.get_page(url)
        if not soup:
            self.logger.error("Falha ao carregar página de pilotos")
            return drivers
        
        # Busca os cards dos pilotos
        driver_cards = soup.find_all('div', class_=re.compile(r'driver.*card|listing.*item'))
        
        if not driver_cards:
            # Tenta um seletor alternativo
            driver_cards = soup.find_all('a', href=re.compile(r'/drivers/'))
        
        self.logger.info(f"Encontrados {len(driver_cards)} pilotos")
        
        for card in driver_cards:
            try:
                driver = self._extract_driver_from_card(card)
                if driver and driver.name:
                    # Tenta obter informações detalhadas
                    detailed_driver = self._get_driver_details(card, driver)
                    drivers.append(detailed_driver)
                    
                    # Salva no banco de dados
                    db_manager.insert_driver(detailed_driver)
                    self.logger.info(f"Piloto salvo: {detailed_driver.name}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao processar piloto: {e}")
                continue
        
        return drivers
    
    def _extract_driver_from_card(self, card) -> Optional[Driver]:
        """
        Extrai informações básicas do piloto de um card
        
        Args:
            card: Elemento HTML do card do piloto
            
        Returns:
            Objeto Driver com informações básicas
        """
        driver = Driver()
        
        # Nome do piloto
        name_elem = card.find(['h1', 'h2', 'h3', 'h4'], text=re.compile(r'[A-Z][a-z]+\s+[A-Z][a-z]+'))
        if not name_elem:
            name_elem = card.find('span', class_=re.compile(r'name|driver'))
        
        if name_elem:
            driver.name = self.clean_text(name_elem.get_text())
        
        # Número do piloto
        number_elem = card.find(text=re.compile(r'#?\d{1,2}'))
        if number_elem:
            driver.number = self.parse_number(number_elem)
        
        # Equipe
        team_elem = card.find(['span', 'div'], class_=re.compile(r'team|constructor'))
        if team_elem:
            driver.team = self.clean_text(team_elem.get_text())
        
        return driver
    
    def _get_driver_details(self, card, basic_driver: Driver) -> Driver:
        """
        Obtém informações detalhadas do piloto
        
        Args:
            card: Elemento HTML do card do piloto
            basic_driver: Objeto Driver com informações básicas
            
        Returns:
            Objeto Driver com informações detalhadas
        """
        driver = basic_driver
        
        # Tenta encontrar link para página do piloto
        link_elem = card.find('a', href=True)
        if link_elem:
            driver_url = urljoin(self.base_url, link_elem['href'])
            detailed_soup = self.get_page(driver_url)
            
            if detailed_soup:
                # Extrai informações da página do piloto
                self._extract_detailed_info(detailed_soup, driver)
        
        return driver
    
    def _extract_detailed_info(self, soup, driver: Driver):
        """
        Extrai informações detalhadas da página do piloto
        
        Args:
            soup: BeautifulSoup da página do piloto
            driver: Objeto Driver para atualizar
        """
        # Nacionalidade
        country_elem = soup.find(text=re.compile(r'Country|Nationality'))
        if country_elem:
            parent = country_elem.parent
            if parent:
                driver.nationality = self.clean_text(parent.get_text())
        
        # Data de nascimento
        birth_elem = soup.find(text=re.compile(r'Date of birth|Born'))
        if birth_elem:
            try:
                # Procura por padrões de data
                date_pattern = r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}'
                date_match = re.search(date_pattern, birth_elem.parent.get_text())
                if date_match:
                    date_str = date_match.group()
                    # Tenta diferentes formatos de data
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                        try:
                            driver.date_of_birth = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
            except Exception as e:
                self.logger.warning(f"Erro ao parsear data de nascimento: {e}")
        
        # Estatísticas (vitórias, pódios, pontos)
        stats_section = soup.find('div', class_=re.compile(r'stats|statistics'))
        if stats_section:
            # Vitórias
            wins_elem = stats_section.find(text=re.compile(r'Wins?'))
            if wins_elem:
                driver.wins = self.parse_number(wins_elem.parent.get_text()) or 0
            
            # Pódios
            podiums_elem = stats_section.find(text=re.compile(r'Podiums?'))
            if podiums_elem:
                driver.podiums = self.parse_number(podiums_elem.parent.get_text()) or 0
            
            # Pontos
            points_elem = stats_section.find(text=re.compile(r'Points?'))
            if points_elem:
                driver.points = self.parse_number(points_elem.parent.get_text()) or 0
            
            # Campeonatos
            championships_elem = stats_section.find(text=re.compile(r'Championships?|World titles?'))
            if championships_elem:
                driver.championships = self.parse_number(championships_elem.parent.get_text()) or 0
    
    def scrape_driver_standings(self, db_manager: DatabaseManager, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Coleta a classificação atual dos pilotos
        
        Args:
            db_manager: Instância do gerenciador do banco de dados
            season: Temporada (None para atual)
            
        Returns:
            Lista de dicionários com classificação
        """
        if season is None:
            season = datetime.now().year
        
        standings_url = f"{self.base_url}/en/results.html/{season}/drivers.html"
        
        soup = self.get_page(standings_url)
        if not soup:
            self.logger.error("Falha ao carregar página de classificação")
            return []
        
        standings = []
        
        # Busca tabela de classificação
        table = soup.find('table', class_=re.compile(r'standings|results'))
        if not table:
            # Tenta buscar por estrutura alternativa
            table = soup.find('div', class_=re.compile(r'standings|results'))
        
        if table:
            rows = table.find_all('tr')[1:]  # Pula cabeçalho
            
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        position = self.parse_number(cells[0].get_text()) or 0
                        driver_name = self.clean_text(cells[1].get_text())
                        points = self.parse_number(cells[-1].get_text()) or 0
                        
                        standings.append({
                            'position': position,
                            'driver_name': driver_name,
                            'points': points,
                            'season': season
                        })
                        
                except Exception as e:
                    self.logger.error(f"Erro ao processar linha da classificação: {e}")
                    continue
        
        return standings


def main():
    """Função principal para executar o scraper de pilotos"""
    import logging
    import os
    from dotenv import load_dotenv
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Inicializa banco de dados
    db_path = os.getenv('DATABASE_PATH', 'data/f1_database.db')
    db_manager = DatabaseManager(db_path)
    
    # Executa scraper
    scraper = DriversScraper()
    drivers = scraper.scrape_all_drivers(db_manager)
    
    print(f"Coletados dados de {len(drivers)} pilotos")
    
    # Coleta classificação
    standings = scraper.scrape_driver_standings(db_manager)
    print(f"Coletada classificação com {len(standings)} entradas")


if __name__ == "__main__":
    main()
