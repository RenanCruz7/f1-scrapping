"""
Gerenciador do banco de dados SQLite para o projeto F1
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from ..models import Driver, Team


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
                    team TEXT,
                    points INTEGER DEFAULT 0,
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
                    points INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de corridas (simplificada)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS races (
                    race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    season INTEGER NOT NULL,
                    round_number INTEGER NOT NULL,
                    race_name TEXT NOT NULL,
                    circuit_name TEXT,
                    country TEXT,
                    date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(season, round_number)
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
                (name, nationality, team, points, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                driver.name, driver.nationality, driver.team, driver.points, datetime.now()
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
                (name, points, updated_at)
                VALUES (?, ?, ?)
            """, (
                team.name, team.points, datetime.now()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def insert_race(self, season: int, round_number: int, race_name: str, 
                   circuit_name: str = "", country: str = "", date: str = "") -> Optional[int]:
        """
        Insere uma corrida no banco de dados
        
        Args:
            season: Temporada da corrida
            round_number: Número da etapa
            race_name: Nome da corrida
            circuit_name: Nome do circuito
            country: País da corrida
            date: Data da corrida
            
        Returns:
            ID da corrida inserida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO races 
                (season, round_number, race_name, circuit_name, country, date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                season, round_number, race_name, circuit_name, country, date, datetime.now()
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
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as equipes do banco
        
        Returns:
            Lista de dicionários com dados das equipes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams ORDER BY points DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_races_by_season(self, season: int) -> List[Dict[str, Any]]:
        """
        Retorna todas as corridas de uma temporada
        
        Args:
            season: Temporada
            
        Returns:
            Lista de corridas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM races 
                WHERE season = ? 
                ORDER BY round_number
            """, (season,))
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
    
    def update_driver_points(self, driver_name: str, points: int) -> bool:
        """
        Atualiza os pontos de um piloto
        
        Args:
            driver_name: Nome do piloto
            points: Novos pontos
            
        Returns:
            True se atualizado com sucesso
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE drivers 
                SET points = ?, updated_at = ?
                WHERE name = ?
            """, (points, datetime.now(), driver_name))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def update_team_points(self, team_name: str, points: int) -> bool:
        """
        Atualiza os pontos de uma equipe
        
        Args:
            team_name: Nome da equipe
            points: Novos pontos
            
        Returns:
            True se atualizado com sucesso
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE teams 
                SET points = ?, updated_at = ?
                WHERE name = ?
            """, (points, datetime.now(), team_name))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_drivers_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Retorna pilotos de uma equipe específica
        
        Args:
            team_name: Nome da equipe
            
        Returns:
            Lista de pilotos da equipe
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM drivers 
                WHERE team = ? 
                ORDER BY points DESC
            """, (team_name,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_championship_standings(self) -> List[Dict[str, Any]]:
        """
        Retorna classificação do campeonato de pilotos
        
        Returns:
            Lista ordenada por pontos
        """
        return self.get_all_drivers()
    
    def get_constructors_standings(self) -> List[Dict[str, Any]]:
        """
        Retorna classificação do campeonato de construtores
        
        Returns:
            Lista ordenada por pontos
        """
        return self.get_all_teams()
    
    def database_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do banco de dados
        
        Returns:
            Dicionário com estatísticas
        """
        drivers = self.get_all_drivers()
        teams = self.get_all_teams()
        
        return {
            "total_drivers": len(drivers),
            "total_teams": len(teams),
            "top_driver": drivers[0] if drivers else None,
            "top_team": teams[0] if teams else None,
            "total_points_drivers": sum(d["points"] for d in drivers),
            "total_points_teams": sum(t["points"] for t in teams)
        }

    def cleanup_old_data(self, days: int = 30):
        """
        Remove dados antigos do banco
        
        Args:
            days: Número de dias para manter os dados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM races 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
