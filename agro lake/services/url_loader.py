"""Módulo para carregamento e validação de URLs."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_url(url: str) -> bool:
    """
    Valida o formato de uma URL.
    
    Suporta http://, https://, localhost, IPs.
    
    Args:
        url: URL a ser validada
        
    Returns:
        True se a URL for válida, False caso contrário
    """
    if not url or not isinstance(url, str):
        return False
    
    # Padrão regex para validar URLs
    # Suporta: http://, https://, localhost, IPs (IPv4)
    url_pattern = re.compile(
        r'^https?://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domínio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$',  # path opcional
        re.IGNORECASE
    )
    
    try:
        return bool(url_pattern.match(url.strip()))
    except Exception as e:
        logger.debug(f"Erro ao validar URL '{url}': {e}")
        return False


def load_urls_from_json(json_path: Path) -> Dict[str, Any]:
    """
    Carrega e valida arquivo urls.json.
    
    Garante estrutura válida (tutoriais e urls).
    Valida todas as URLs.
    Retorna estrutura padrão se arquivo não existir.
    
    Args:
        json_path: Caminho para o arquivo urls.json
        
    Returns:
        Dicionário com estrutura de tutoriais e URLs
    """
    default_structure = {
        "tutoriais": [],
        "urls": []
    }
    
    # Se o arquivo não existir, retornar estrutura padrão
    if not json_path.exists():
        logger.info(f"Arquivo {json_path} não encontrado. Retornando estrutura padrão.")
        return default_structure
    
    try:
        # Ler e fazer parse do JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar estrutura básica
        if not isinstance(data, dict):
            logger.warning(f"Arquivo {json_path} não contém um objeto JSON válido. Retornando estrutura padrão.")
            return default_structure
        
        # Garantir que 'tutoriais' e 'urls' existam
        if "tutoriais" not in data:
            data["tutoriais"] = []
        if "urls" not in data:
            data["urls"] = []
        
        # Validar que são listas
        if not isinstance(data["tutoriais"], list):
            logger.warning(f"Campo 'tutoriais' em {json_path} não é uma lista. Convertendo.")
            data["tutoriais"] = []
        if not isinstance(data["urls"], list):
            logger.warning(f"Campo 'urls' em {json_path} não é uma lista. Convertendo.")
            data["urls"] = []
        
        # Validar URLs em tutoriais
        valid_tutoriais = []
        for tutorial in data["tutoriais"]:
            if not isinstance(tutorial, dict):
                logger.warning(f"Tutorial inválido ignorado: {tutorial}")
                continue
            
            if "url" not in tutorial or not validate_url(tutorial.get("url", "")):
                logger.warning(f"Tutorial com URL inválida ignorado: {tutorial.get('titulo', 'Sem título')}")
                continue
            
            # Garantir campos obrigatórios
            tutorial_valid = {
                "titulo": tutorial.get("titulo", "Sem título"),
                "url": tutorial.get("url", ""),
                "categoria": tutorial.get("categoria", ""),
                "topicos": tutorial.get("topicos", [])
            }
            
            if not isinstance(tutorial_valid["topicos"], list):
                tutorial_valid["topicos"] = []
            
            valid_tutoriais.append(tutorial_valid)
        
        data["tutoriais"] = valid_tutoriais
        
        # Validar URLs em urls
        valid_urls = []
        for url_item in data["urls"]:
            if not isinstance(url_item, dict):
                logger.warning(f"URL inválida ignorada: {url_item}")
                continue
            
            if "url" not in url_item or not validate_url(url_item.get("url", "")):
                logger.warning(f"URL inválida ignorada: {url_item.get('url', 'Sem URL')}")
                continue
            
            # Garantir campos obrigatórios
            url_valid = {
                "url": url_item.get("url", ""),
                "descricao": url_item.get("descricao", ""),
                "categoria": url_item.get("categoria", ""),
                "topicos": url_item.get("topicos", [])
            }
            
            if not isinstance(url_valid["topicos"], list):
                url_valid["topicos"] = []
            
            valid_urls.append(url_valid)
        
        data["urls"] = valid_urls
        
        logger.info(f"Carregado {len(data['tutoriais'])} tutoriais e {len(data['urls'])} URLs de {json_path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer parse do JSON em {json_path}: {e}")
        return default_structure
    except Exception as e:
        logger.error(f"Erro ao carregar {json_path}: {e}")
        return default_structure


def filter_urls_by_category(data: Dict[str, Any], category: Optional[str] = None) -> Dict[str, Any]:
    """
    Filtra tutoriais e URLs por categoria.
    
    Args:
        data: Dados carregados de urls.json
        category: Categoria para filtrar (case-insensitive)
        
    Returns:
        Dicionário filtrado com tutoriais e URLs da categoria
    """
    if not category:
        return data
    
    category_lower = category.lower().strip()
    
    # Filtrar tutoriais
    filtered_tutoriais = [
        t for t in data.get("tutoriais", [])
        if t.get("categoria", "").lower() == category_lower
    ]
    
    # Filtrar URLs
    filtered_urls = [
        u for u in data.get("urls", [])
        if u.get("categoria", "").lower() == category_lower
    ]
    
    return {
        "tutoriais": filtered_tutoriais,
        "urls": filtered_urls
    }

