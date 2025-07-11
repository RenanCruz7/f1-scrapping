"""
Scraper para dados de corridas de F1
"""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from . import BaseScraper
from ..models import Race, RaceResult
from ..database import DatabaseManager


class RacesScraper(BaseScraper):
    """Scraper para coletar informações das corridas de F1"""
    
    def __init__(self):
        super().__init__("https://www.formula1.com")
        self.races_endpoint = "/en/racing/{}/races.html"
    
    def scrape_season_races(self, db_manager: DatabaseManager, season: Optional[int] = None) -> List[Race]:
        """
        Coleta informações de todas as corridas de uma temporada
        
        Args:
            db_manager: Instância do gerenciador do banco de dados
            season: Ano da temporada (None para atual)
            
        Returns:
            Lista de objetos Race
        """
        if season is None:
            season = datetime.now().year
        
        races = []
        url = urljoin(self.base_url, self.races_endpoint.format(season))
        
        soup = self.get_page(url)
        if not soup:
            self.logger.error(f"Falha ao carregar página de corridas para {season}")
            return races
        
        # Busca os cards das corridas
        race_cards = soup.find_all(['div', 'article'], class_=re.compile(r'race.*card|event.*item|listing.*item'))
        
        if not race_cards:
            # Tenta seletor alternativo
            race_cards = soup.find_all('a', href=re.compile(r'/races/'))
        
        self.logger.info(f"Encontradas {len(race_cards)} corridas para {season}")
        
        for i, card in enumerate(race_cards, 1):
            try:
                race = self._extract_race_from_card(card, season, i)
                if race and race.race_name:
                    # Tenta obter informações detalhadas
                    detailed_race = self._get_race_details(card, race)
                    races.append(detailed_race)
                    
                    # Salva no banco de dados
                    db_manager.insert_race(detailed_race)
                    self.logger.info(f"Corrida salva: {detailed_race.race_name}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao processar corrida: {e}")
                continue
        
        return races
    
    def _extract_race_from_card(self, card, season: int, round_number: int) -> Optional[Race]:
        """
        Extrai informações básicas da corrida de um card
        
        Args:
            card: Elemento HTML do card da corrida
            season: Temporada
            round_number: Número da etapa
            
        Returns:
            Objeto Race com informações básicas
        """
        race = Race()
        race.season = season
        race.round_number = round_number
        
        # Nome da corrida
        name_elem = card.find(['h1', 'h2', 'h3', 'h4'])
        if not name_elem:
            name_elem = card.find(['span', 'div'], class_=re.compile(r'name|title|event'))
        
        if name_elem:
            race.race_name = self.clean_text(name_elem.get_text())
        
        # País/Local
        country_elem = card.find(['span', 'div'], class_=re.compile(r'country|location|circuit'))
        if country_elem:
            race.country = self.clean_text(country_elem.get_text())
        
        # Data da corrida
        date_elem = card.find(text=re.compile(r'\d{1,2}[\/\-\.]\d{1,2}|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'))
        if date_elem:
            try:
                race.date = self._parse_race_date(date_elem)
            except Exception as e:
                self.logger.warning(f"Erro ao parsear data da corrida: {e}")
        
        return race
    
    def _parse_race_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse da data da corrida
        
        Args:
            date_text: Texto contendo a data
            
        Returns:
            Objeto datetime ou None se não conseguir parsear
        """
        if not date_text:
            return None
        
        # Limpa o texto
        date_str = self.clean_text(str(date_text))
        
        # Padrões de data para tentar
        date_patterns = [
            (r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})', ['%d/%m/%Y', '%m/%d/%Y']),
            (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', ['%d %b %Y']),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})', ['%b %d %Y']),
        ]
        
        for pattern, formats in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                for fmt in formats:
                    try:
                        return datetime.strptime(match.group(), fmt)
                    except ValueError:
                        continue
        
        return None
    
    def _get_race_details(self, card, basic_race: Race) -> Race:
        """
        Obtém informações detalhadas da corrida
        
        Args:
            card: Elemento HTML do card da corrida
            basic_race: Objeto Race com informações básicas
            
        Returns:
            Objeto Race com informações detalhadas
        """
        race = basic_race
        
        # Tenta encontrar link para página da corrida
        link_elem = card.find('a', href=True)
        if link_elem:
            race_url = urljoin(self.base_url, link_elem['href'])
            detailed_soup = self.get_page(race_url)
            
            if detailed_soup:
                # Extrai informações da página da corrida
                self._extract_detailed_race_info(detailed_soup, race)
        
        return race
    
    def _extract_detailed_race_info(self, soup, race: Race):
        """
        Extrai informações detalhadas da página da corrida
        
        Args:
            soup: BeautifulSoup da página da corrida
            race: Objeto Race para atualizar
        """
        # Nome do circuito
        circuit_elem = soup.find(text=re.compile(r'Circuit|Track'))
        if circuit_elem and circuit_elem.parent:
            race.circuit_name = self.clean_text(circuit_elem.parent.get_text())
        
        # Número de voltas
        laps_elem = soup.find(text=re.compile(r'Laps?'))
        if laps_elem:
            race.laps = self.parse_number(laps_elem.parent.get_text()) or 0
        
        # Distância
        distance_elem = soup.find(text=re.compile(r'Distance|Length'))
        if distance_elem and distance_elem.parent:
            race.distance = self.clean_text(distance_elem.parent.get_text())
        
        # Tempo de corrida
        race_time_elem = soup.find(text=re.compile(r'Race time|Duration'))
        if race_time_elem and race_time_elem.parent:
            race.race_time = self.clean_text(race_time_elem.parent.get_text())
        
        # Volta mais rápida
        fastest_lap_elem = soup.find(text=re.compile(r'Fastest lap'))
        if fastest_lap_elem and fastest_lap_elem.parent:
            race.fastest_lap = self.clean_text(fastest_lap_elem.parent.get_text())
    
    def scrape_race_results(self, db_manager: DatabaseManager, season: Optional[int] = None, race_name: Optional[str] = None) -> List[RaceResult]:
        """
        Coleta resultados de corridas
        
        Args:
            db_manager: Instância do gerenciador do banco de dados
            season: Temporada
            race_name: Nome específico da corrida (None para todas)
            
        Returns:
            Lista de objetos RaceResult
        """
        if season is None:
            season = datetime.now().year
        
        results = []
        results_url = f"{self.base_url}/en/results.html/{season}/races.html"
        
        soup = self.get_page(results_url)
        if not soup:
            self.logger.error(f"Falha ao carregar resultados para {season}")
            return results
        
        # Busca links para resultados individuais das corridas
        race_links = soup.find_all('a', href=re.compile(r'/results/.*/{}/races/'.format(season)))
        
        for link in race_links:
            try:
                race_url = urljoin(self.base_url, link['href'])
                race_results = self._scrape_single_race_results(race_url, db_manager)
                results.extend(race_results)
                
            except Exception as e:
                self.logger.error(f"Erro ao processar resultados da corrida: {e}")
                continue
        
        return results
    
    def _scrape_single_race_results(self, race_url: str, db_manager: DatabaseManager) -> List[RaceResult]:
        """
        Coleta resultados de uma corrida específica
        
        Args:
            race_url: URL da página de resultados
            db_manager: Gerenciador do banco de dados
            
        Returns:
            Lista de resultados da corrida
        """
        results = []
        
        soup = self.get_page(race_url)
        if not soup:
            return results
        
        # Busca tabela de resultados
        table = soup.find('table', class_=re.compile(r'results|classification'))
        if not table:
            return results
        
        rows = table.find_all('tr')[1:]  # Pula cabeçalho
        
        for row in rows:
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:
                    result = RaceResult()
                    
                    # Posição
                    result.position = self.parse_number(cells[0].get_text())
                    
                    # Nome do piloto (usado para buscar driver_id)
                    driver_name = self.clean_text(cells[1].get_text())
                    
                    # Equipe (usado para buscar team_id)
                    team_name = self.clean_text(cells[2].get_text())
                    
                    # Pontos
                    result.points = self.parse_number(cells[-1].get_text()) or 0
                    
                    # Tempo/Status
                    if len(cells) > 5:
                        result.time = self.clean_text(cells[4].get_text())
                        result.status = self.clean_text(cells[5].get_text()) if len(cells) > 6 else "Finished"
                    
                    # Busca IDs no banco
                    driver_data = db_manager.get_driver_by_name(driver_name)
                    if driver_data:
                        result.driver_id = driver_data['driver_id']
                    
                    team_data = db_manager.get_team_by_name(team_name)
                    if team_data:
                        result.team_id = team_data['team_id']
                    
                    if result.driver_id and result.team_id:
                        results.append(result)
                        
            except Exception as e:
                self.logger.error(f"Erro ao processar resultado: {e}")
                continue
        
        return results


def main():
    """Função principal para executar o scraper de corridas"""
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
    scraper = RacesScraper()
    
    # Coleta corridas da temporada atual
    races = scraper.scrape_season_races(db_manager)
    print(f"Coletados dados de {len(races)} corridas")
    
    # Coleta resultados
    results = scraper.scrape_race_results(db_manager)
    print(f"Coletados {len(results)} resultados de corridas")


if __name__ == "__main__":
    main()
