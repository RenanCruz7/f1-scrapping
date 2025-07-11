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
    team: str = ""
    points: int = 0


@dataclass
class Team:
    """Modelo para representar uma equipe de F1"""
    team_id: Optional[int] = None
    name: str = ""
    points: int = 0

