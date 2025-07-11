"""
Utilitários para o projeto F1 Scraping
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Configura o sistema de logging
    
    Args:
        log_file: Caminho para o arquivo de log
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Logger configurado
    """
    # Cria diretório de logs se não existir
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configuração do formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger principal
    logger = logging.getLogger('f1_scraper')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def validate_environment():
    """
    Valida se todas as variáveis de ambiente necessárias estão configuradas
    
    Raises:
        EnvironmentError: Se alguma variável obrigatória estiver faltando
    """
    required_vars = ['DATABASE_PATH']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(
            f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}"
        )


def get_current_season() -> int:
    """
    Retorna a temporada atual de F1
    
    Returns:
        Ano da temporada atual
    """
    now = datetime.now()
    
    # Se estivermos antes de março, considera o ano anterior como temporada atual
    if now.month < 3:
        return now.year - 1
    
    return now.year


def format_time(seconds: float) -> str:
    """
    Formata tempo em segundos para formato legível
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        String formatada (ex: "1:23.456")
    """
    if seconds < 60:
        return f"{seconds:.3f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    return f"{minutes}:{remaining_seconds:06.3f}"


def clean_driver_name(name: str) -> str:
    """
    Limpa e padroniza nome de piloto
    
    Args:
        name: Nome bruto do piloto
        
    Returns:
        Nome limpo e padronizado
    """
    if not name:
        return ""
    
    # Remove caracteres especiais e espaços extras
    cleaned = " ".join(name.split())
    
    # Remove prefixos comuns
    prefixes_to_remove = ["Mr.", "Sir", "Dr."]
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Capitaliza corretamente
    return cleaned.title()


def clean_team_name(name: str) -> str:
    """
    Limpa e padroniza nome de equipe
    
    Args:
        name: Nome bruto da equipe
        
    Returns:
        Nome limpo e padronizado
    """
    if not name:
        return ""
    
    # Remove texto comum de sufixos
    suffixes_to_remove = [" F1 Team", " Racing", " Formula 1 Team"]
    
    cleaned = name.strip()
    for suffix in suffixes_to_remove:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
    
    return cleaned


def parse_position(position_text: str) -> Optional[int]:
    """
    Extrai posição de um texto
    
    Args:
        position_text: Texto contendo posição
        
    Returns:
        Posição como inteiro ou None se não encontrado
    """
    if not position_text:
        return None
    
    # Remove texto não numérico
    import re
    match = re.search(r'(\d+)', position_text.strip())
    
    if match:
        try:
            position = int(match.group(1))
            return position if 1 <= position <= 30 else None  # Validação básica
        except ValueError:
            return None
    
    return None


def parse_points(points_text: str) -> int:
    """
    Extrai pontos de um texto
    
    Args:
        points_text: Texto contendo pontos
        
    Returns:
        Pontos como inteiro (0 se não encontrado)
    """
    if not points_text:
        return 0
    
    import re
    match = re.search(r'(\d+(?:\.\d+)?)', points_text.strip())
    
    if match:
        try:
            return int(float(match.group(1)))
        except ValueError:
            return 0
    
    return 0


def is_valid_lap_time(lap_time: str) -> bool:
    """
    Valida se um tempo de volta está em formato correto
    
    Args:
        lap_time: Tempo de volta (ex: "1:23.456")
        
    Returns:
        True se válido, False caso contrário
    """
    if not lap_time:
        return False
    
    import re
    # Padrão para tempo de volta: minutos:segundos.milissegundos
    pattern = r'^\d{1,2}:\d{2}\.\d{3}$'
    
    return bool(re.match(pattern, lap_time.strip()))


def create_backup(db_path: str) -> str:
    """
    Cria backup do banco de dados
    
    Args:
        db_path: Caminho para o banco de dados
        
    Returns:
        Caminho do arquivo de backup
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")
    
    # Nome do backup com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"
    backup_path = os.path.join(os.path.dirname(db_path), backup_name)
    
    # Copia arquivo
    import shutil
    shutil.copy2(db_path, backup_path)
    
    return backup_path


class ProgressTracker:
    """Classe para rastrear progresso de operações"""
    
    def __init__(self, total: int, description: str = "Progresso"):
        """
        Inicializa o tracker de progresso
        
        Args:
            total: Total de itens a processar
            description: Descrição da operação
        """
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """
        Atualiza o progresso
        
        Args:
            increment: Quantidade a incrementar
        """
        self.current += increment
        
        # Calcula porcentagem e tempo estimado
        percentage = (self.current / self.total) * 100
        elapsed = datetime.now() - self.start_time
        
        if self.current > 0:
            estimated_total = elapsed * (self.total / self.current)
            remaining = estimated_total - elapsed
            
            print(f"\r{self.description}: {self.current}/{self.total} "
                  f"({percentage:.1f}%) - Restante: {remaining}", end="")
        
        if self.current >= self.total:
            print(f"\n{self.description} concluído em {elapsed}")
    
    def finish(self):
        """Finaliza o tracker"""
        self.current = self.total
        elapsed = datetime.now() - self.start_time
        print(f"\n{self.description} concluído em {elapsed}")
