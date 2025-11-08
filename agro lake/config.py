"""Configurações e variáveis de ambiente para o servidor MCP Seagri."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Classe de configuração centralizada."""
    
    # Configurações do servidor MCP
    SERVER_NAME: str = os.getenv("SERVER_NAME", "Seagri Agricultural Server")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Configurações do Apidog
    APIDOG_ACCESS_TOKEN: Optional[str] = os.getenv("APIDOG_ACCESS_TOKEN")
    APIDOG_PROJECT_ID: Optional[str] = os.getenv("APIDOG_PROJECT_ID", "1119125")
    APIDOG_BASE_URL: str = os.getenv("APIDOG_BASE_URL", "http://127.0.0.1:3658/m1/1119125-1110256-default")
    
    # Configurações do Google Gemini
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    GEMINI_MAX_OUTPUT_TOKENS: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    
    # Configurações do HGBrasil
    HG_BRASIL_API_KEY: Optional[str] = os.getenv("HG_BRASIL_API_KEY")
    HG_BRASIL_BASE_URL: str = os.getenv("HG_BRASIL_BASE_URL", "https://api.hgbrasil.com/weather")
    
    # Configurações de API (se necessário)
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    API_MAX_RETRIES: int = int(os.getenv("API_MAX_RETRIES", "3"))
    
    # Configurações de segurança
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Configurações do cliente GUI
    GUI_THEME: str = os.getenv("GUI_THEME", "dark")
    GUI_WIDTH: int = int(os.getenv("GUI_WIDTH", "1200"))
    GUI_HEIGHT: int = int(os.getenv("GUI_HEIGHT", "800"))
    
    # Configurações do DocsManager
    MCP_DISABLE_RCLONE_SYNC: bool = os.getenv("MCP_DISABLE_RCLONE_SYNC", "false").lower() == "true"
    MCP_RCLONE_TIMEOUT: int = int(os.getenv("MCP_RCLONE_TIMEOUT", "60"))
    MCP_URL_CACHE_TTL_HOURS: float = float(os.getenv("MCP_URL_CACHE_TTL_HOURS", "1.0"))
    MCP_URL_CACHE_MAX_SIZE: int = int(os.getenv("MCP_URL_CACHE_MAX_SIZE", "1000"))
    MCP_DISABLE_URL_CACHE: bool = os.getenv("MCP_DISABLE_URL_CACHE", "false").lower() == "true"
    MCP_URL_FETCH_TIMEOUT: int = int(os.getenv("MCP_URL_FETCH_TIMEOUT", "10"))
    
    @classmethod
    def validate(cls) -> None:
        """Valida se as configurações obrigatórias estão presentes."""
        if not cls.APIDOG_ACCESS_TOKEN:
            raise ValueError(
                "APIDOG_ACCESS_TOKEN não configurado. "
                "Configure no arquivo .env ou variável de ambiente."
            )


# Instância global de configuração
config = Config()

