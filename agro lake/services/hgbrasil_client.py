"""Cliente para integração com HGBrasil Weather API."""

import logging
import urllib.parse
import urllib.request
import json
from typing import Dict, Any, Optional

from config import config

logger = logging.getLogger(__name__)


class HGBrasilClient:
    """Cliente para interagir com HGBrasil Weather API."""
    
    def __init__(self):
        """Inicializa o cliente HGBrasil."""
        self.base_url = config.HG_BRASIL_BASE_URL
        self.api_key = config.HG_BRASIL_API_KEY
        self.timeout = config.API_TIMEOUT
        
    def is_available(self) -> bool:
        """Verifica se o cliente está disponível."""
        return self.api_key is not None and len(self.api_key) > 0
    
    async def get_weather(
        self,
        city_name: str = "Brasilia,DF",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém dados meteorológicos de uma cidade.
        
        Args:
            city_name: Nome da cidade no formato "Cidade,UF" (ex: "Brasilia,DF")
            api_key: Chave de API (opcional, usa a configurada se não fornecida)
            
        Returns:
            Dicionário com dados meteorológicos atuais e previsão
        """
        try:
            # Usar API key fornecida ou a configurada
            key = api_key or self.api_key or ""
            
            params = {
                'format': 'json',
                'city_name': city_name,
                'key': key,
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            
            logger.info(f"Buscando dados meteorológicos para: {city_name}")
            
            # Fazer requisição HTTP
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                raw = resp.read()
                payload = json.loads(raw.decode('utf-8'))
            
            # Normalizar resposta
            results = payload.get('results') or {}
            current = {
                'temp': results.get('temp'),
                'description': results.get('description'),
                'city': results.get('city'),
                'humidity': results.get('humidity'),
                'wind_speedy': results.get('wind_speedy'),
                'time': results.get('time'),
                'date': results.get('date'),
                'condition_code': results.get('condition_code'),
                'condition_slug': results.get('condition_slug'),
                'sunrise': results.get('sunrise'),
                'sunset': results.get('sunset'),
                'cloudiness': results.get('cloudiness'),
            }
            
            forecast = results.get('forecast') or []
            
            return {
                'ok': True,
                'provider': 'HG Brasil',
                'query': {'city_name': city_name},
                'current': current,
                'forecast': forecast,
                'status': 'success'
            }
            
        except urllib.error.HTTPError as e:
            logger.error(f"Erro HTTP ao buscar dados meteorológicos: {e}")
            return {
                'ok': False,
                'error': f"Erro HTTP: {str(e)}",
                'status': 'error'
            }
        except urllib.error.URLError as e:
            logger.error(f"Erro de URL ao buscar dados meteorológicos: {e}")
            return {
                'ok': False,
                'error': f"Erro de conexão: {str(e)}",
                'status': 'error'
            }
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            return {
                'ok': False,
                'error': f"Erro ao processar resposta: {str(e)}",
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar dados meteorológicos: {e}")
            return {
                'ok': False,
                'error': str(e),
                'status': 'error'
            }
    
    async def get_weather_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtém dados meteorológicos por coordenadas.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            api_key: Chave de API (opcional)
            
        Returns:
            Dicionário com dados meteorológicos
        """
        try:
            key = api_key or self.api_key or ""
            
            params = {
                'format': 'json',
                'lat': latitude,
                'lon': longitude,
                'key': key,
            }
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            
            logger.info(f"Buscando dados meteorológicos para coordenadas: {latitude}, {longitude}")
            
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                raw = resp.read()
                payload = json.loads(raw.decode('utf-8'))
            
            results = payload.get('results') or {}
            current = {
                'temp': results.get('temp'),
                'description': results.get('description'),
                'city': results.get('city'),
                'humidity': results.get('humidity'),
                'wind_speedy': results.get('wind_speedy'),
                'time': results.get('time'),
                'date': results.get('date'),
            }
            
            forecast = results.get('forecast') or []
            
            return {
                'ok': True,
                'provider': 'HG Brasil',
                'query': {'latitude': latitude, 'longitude': longitude},
                'current': current,
                'forecast': forecast,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados por coordenadas: {e}")
            return {
                'ok': False,
                'error': str(e),
                'status': 'error'
            }

