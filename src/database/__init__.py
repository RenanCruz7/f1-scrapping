"""
Gerenciador do banco de dados SQLite para o projeto F1
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from ..models import Driver, Team, Race, RaceResult, StandingsEntry


class DatabaseManager:
    """Classe para gerenciar operações no banco de dados"""
    
    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador do banco de dados
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self):
        """Garante que o diretório do banco de dados existe"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Cria as tabelas do banco de dados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de pilotos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    nationality TEXT,
                    date_of_birth DATE,
                    number INTEGER,
                    team TEXT,
                    points INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    podiums INTEGER DEFAULT 0,
                    championships INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, nationality)
                )
            """)
            
            # Tabela de equipes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    base TEXT,
                    team_chief TEXT,
                    technical_chief TEXT,
                    chassis TEXT,
                    power_unit TEXT,
                    first_team_entry INTEGER,
                    world_championships INTEGER DEFAULT 0,
                    highest_race_finish TEXT,
                    pole_positions INTEGER DEFAULT 0,
                    fastest_laps INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de corridas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS races (
                    race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    race_name TEXT NOT NULL,
                    circuit_name TEXT,
                    country TEXT,
                    date DATE,
                    laps INTEGER,
                    distance TEXT,
                    race_time TEXT,
                    fastest_lap TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, round_number)
                )
            """)
            
            # Tabela de resultados de corridas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS race_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    team_id INTEGER NOT NULL,
                    position INTEGER,
                    points INTEGER DEFAULT 0,
                    laps INTEGER,
                    time TEXT,
                    fastest_lap TEXT,
                    fastest_lap_rank INTEGER,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (race_id) REFERENCES races (race_id),
                    FOREIGN KEY (driver_id) REFERENCES drivers (driver_id),
                    FOREIGN KEY (team_id) REFERENCES teams (team_id),
                    UNIQUE(race_id, driver_id)
                )
            """)
            
            # Tabela de classificação do campeonato
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS standings (
                    standing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    team_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    points INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (driver_id) REFERENCES drivers (driver_id),
                    FOREIGN KEY (team_id) REFERENCES teams (team_id),
                    UNIQUE(season, driver_id)
                )
            """)
            
            conn.commit()
    
    def insert_driver(self, driver: Driver) -> Optional[int]:
        """
        Insere um piloto no banco de dados
        
        Args:
            driver: Objeto Driver a ser inserido
            
        Returns:
            ID do piloto inserido
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO drivers 
                (name, nationality, date_of_birth, number, team, points, wins, podiums, championships, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                driver.name, driver.nationality, driver.date_of_birth, driver.number,
                driver.team, driver.points, driver.wins, driver.podiums, 
                driver.championships, datetime.now()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_team(self, team: Team) -> Optional[int]:
        """
        Insere uma equipe no banco de dados
        
        Args:
            team: Objeto Team a ser inserido
            
        Returns:
            ID da equipe inserida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO teams 
                (name, base, team_chief, technical_chief, chassis, power_unit, 
                 first_team_entry, world_championships, highest_race_finish, 
                 pole_positions, fastest_laps, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team.name, team.base, team.team_chief, team.technical_chief,
                team.chassis, team.power_unit, team.first_team_entry,
                team.world_championships, team.highest_race_finish,
                team.pole_positions, team.fastest_laps, datetime.now()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_race(self, race: Race) -> Optional[int]:
        """
        Insere uma corrida no banco de dados
        
        Args:
            race: Objeto Race a ser inserido
            
        Returns:
            ID da corrida inserida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO races 
                (season, round_number, race_name, circuit_name, country, date, 
                 laps, distance, race_time, fastest_lap, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race.season, race.round_number, race.race_name, race.circuit_name,
                race.country, race.date, race.laps, race.distance,
                race.race_time, race.fastest_lap, datetime.now()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_driver_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Busca um piloto pelo nome
        
        Args:
            name: Nome do piloto
            
        Returns:
            Dicionário com dados do piloto ou None se não encontrado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_team_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma equipe pelo nome
        
        Args:
            name: Nome da equipe
            
        Returns:
            Dicionário com dados da equipe ou None se não encontrado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_drivers(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os pilotos do banco
        
        Returns:
            Lista de dicionários com dados dos pilotos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers ORDER BY points DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_current_standings(self, season: int) -> List[Dict[str, Any]]:
        """
        Retorna a classificação atual do campeonato
        
        Args:
            season: Temporada do campeonato
            
        Returns:
            Lista de dicionários com a classificação
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, d.name as driver_name, t.name as team_name
                FROM standings s
                JOIN drivers d ON s.driver_id = d.driver_id
                JOIN teams t ON s.team_id = t.team_id
                WHERE s.season = ?
                ORDER BY s.position
            """, (season,))
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 30):
        """
        Remove dados antigos do banco
        
        Args:
            days: Número de dias para manter os dados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM race_results 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
