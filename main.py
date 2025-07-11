#!/usr/bin/env python3
"""
Script principal para o projeto F1 Web Scraping

Este script coordena a coleta de dados de F1 de várias fontes e 
armazena no banco de dados SQLite.
"""
import os
import sys
import argparse
import schedule
import time
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager
from src.scrapers.drivers_scraper import DriversScraper
from src.scrapers.races_scraper import RacesScraper
from src.utils import setup_logging, validate_environment, get_current_season, ProgressTracker


class F1ScrapingManager:
    """Classe principal para gerenciar o scraping de dados de F1"""
    
    def __init__(self):
        """Inicializa o gerenciador de scraping"""
        # Carrega variáveis de ambiente
        load_dotenv()
        
        # Valida ambiente
        validate_environment()
        
        # Configura logging
        log_file = os.getenv('LOG_FILE', 'logs/f1_scraper.log')
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.logger = setup_logging(log_file, log_level)
        
        # Inicializa banco de dados
        db_path = os.getenv('DATABASE_PATH', 'data/f1_database.db')
        self.db_manager = DatabaseManager(db_path)
        
        # Inicializa scrapers
        self.drivers_scraper = DriversScraper()
        self.races_scraper = RacesScraper()
        
        self.logger.info("F1 Scraping Manager inicializado")
    
    def scrape_all_data(self, season: Optional[int] = None):
        """
        Executa scraping completo de dados
        
        Args:
            season: Temporada para coletar (None para atual)
        """
        if season is None:
            season = get_current_season()
        
        self.logger.info(f"Iniciando coleta completa de dados para temporada {season}")
        
        try:
            # 1. Coleta dados dos pilotos
            self.logger.info("Coletando dados dos pilotos...")
            drivers = self.drivers_scraper.scrape_all_drivers(self.db_manager)
            self.logger.info(f"Coletados dados de {len(drivers)} pilotos")
            
            # 2. Coleta dados das corridas
            self.logger.info("Coletando dados das corridas...")
            races = self.races_scraper.scrape_season_races(self.db_manager, season)
            self.logger.info(f"Coletados dados de {len(races)} corridas")
            
            # 3. Coleta classificação dos pilotos
            self.logger.info("Coletando classificação dos pilotos...")
            standings = self.drivers_scraper.scrape_driver_standings(self.db_manager, season)
            self.logger.info(f"Coletada classificação com {len(standings)} entradas")
            
            # 4. Coleta resultados das corridas
            self.logger.info("Coletando resultados das corridas...")
            results = self.races_scraper.scrape_race_results(self.db_manager, season)
            self.logger.info(f"Coletados {len(results)} resultados de corridas")
            
            self.logger.info("Coleta completa de dados finalizada com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante coleta de dados: {e}")
            raise
    
    def scrape_drivers_only(self):
        """Executa scraping apenas dos pilotos"""
        self.logger.info("Iniciando coleta de dados dos pilotos")
        
        try:
            drivers = self.drivers_scraper.scrape_all_drivers(self.db_manager)
            self.logger.info(f"Coletados dados de {len(drivers)} pilotos")
            
            # Coleta classificação também
            standings = self.drivers_scraper.scrape_driver_standings(self.db_manager)
            self.logger.info(f"Coletada classificação com {len(standings)} entradas")
            
        except Exception as e:
            self.logger.error(f"Erro durante coleta de pilotos: {e}")
            raise
    
    def scrape_races_only(self, season: Optional[int] = None):
        """
        Executa scraping apenas das corridas
        
        Args:
            season: Temporada para coletar (None para atual)
        """
        if season is None:
            season = get_current_season()
        
        self.logger.info(f"Iniciando coleta de dados das corridas para temporada {season}")
        
        try:
            races = self.races_scraper.scrape_season_races(self.db_manager, season)
            self.logger.info(f"Coletados dados de {len(races)} corridas")
            
            # Coleta resultados também
            results = self.races_scraper.scrape_race_results(self.db_manager, season)
            self.logger.info(f"Coletados {len(results)} resultados de corridas")
            
        except Exception as e:
            self.logger.error(f"Erro durante coleta de corridas: {e}")
            raise
    
    def show_database_stats(self):
        """Mostra estatísticas do banco de dados"""
        try:
            drivers = self.db_manager.get_all_drivers()
            current_season = get_current_season()
            standings = self.db_manager.get_current_standings(current_season)
            
            print("\n" + "="*50)
            print("ESTATÍSTICAS DO BANCO DE DADOS")
            print("="*50)
            print(f"Total de pilotos: {len(drivers)}")
            print(f"Classificação temporada {current_season}: {len(standings)} entradas")
            
            if drivers:
                print("\nTop 5 pilotos por pontos:")
                for i, driver in enumerate(drivers[:5], 1):
                    print(f"  {i}. {driver['name']} - {driver['points']} pontos ({driver['team']})")
            
            if standings:
                print(f"\nTop 5 classificação {current_season}:")
                for i, entry in enumerate(standings[:5], 1):
                    print(f"  {i}. {entry['driver_name']} - {entry['points']} pontos ({entry['team_name']})")
            
            print("="*50 + "\n")
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar estatísticas: {e}")
    
    def start_scheduled_scraping(self, interval_hours: int = 6):
        """
        Inicia execução agendada do scraping
        
        Args:
            interval_hours: Intervalo em horas entre execuções
        """
        self.logger.info(f"Iniciando scraping agendado a cada {interval_hours} horas")
        
        # Agenda execução
        schedule.every(interval_hours).hours.do(self.scrape_all_data)
        
        # Executa uma vez imediatamente
        self.scrape_all_data()
        
        # Loop principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
                
        except KeyboardInterrupt:
            self.logger.info("Scraping agendado interrompido pelo usuário")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="F1 Web Scraping Tool")
    
    # Comandos principais
    parser.add_argument('command', choices=['all', 'drivers', 'races', 'stats', 'schedule'],
                       help='Comando a executar')
    
    # Opções
    parser.add_argument('--season', type=int, default=None,
                       help='Temporada para coletar (padrão: atual)')
    
    parser.add_argument('--interval', type=int, default=6,
                       help='Intervalo em horas para scraping agendado (padrão: 6)')
    
    parser.add_argument('--verbose', action='store_true',
                       help='Ativa modo verboso')
    
    args = parser.parse_args()
    
    # Configura nível de log se verbose
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    try:
        # Inicializa gerenciador
        manager = F1ScrapingManager()
        
        # Executa comando
        if args.command == 'all':
            manager.scrape_all_data(args.season)
            
        elif args.command == 'drivers':
            manager.scrape_drivers_only()
            
        elif args.command == 'races':
            manager.scrape_races_only(args.season)
            
        elif args.command == 'stats':
            manager.show_database_stats()
            
        elif args.command == 'schedule':
            manager.start_scheduled_scraping(args.interval)
        
        # Mostra estatísticas finais (exceto para comando stats e schedule)
        if args.command not in ['stats', 'schedule']:
            manager.show_database_stats()
        
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário")
        sys.exit(0)
        
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
