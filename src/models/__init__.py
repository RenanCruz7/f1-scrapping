"""
Modelos de dados para o projeto F1 Scraping
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Driver:
    """Modelo para representar um piloto de F1"""
    driver_id: Optional[int] = None
    name: str = ""
    nationality: str = ""
    date_of_birth: Optional[datetime] = None
    number: Optional[int] = None
    team: str = ""
    points: int = 0
    wins: int = 0
    podiums: int = 0
    championships: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Team:
    """Modelo para representar uma equipe de F1"""
    team_id: Optional[int] = None
    name: str = ""
    base: str = ""
    team_chief: str = ""
    technical_chief: str = ""
    chassis: str = ""
    power_unit: str = ""
    first_team_entry: Optional[int] = None
    world_championships: int = 0
    highest_race_finish: str = ""
    pole_positions: int = 0
    fastest_laps: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

