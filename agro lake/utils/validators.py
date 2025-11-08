"""Utilitários para validação de dados."""

import re
from typing import Any, Dict, Optional


def sanitize_input(value: Any) -> Any:
    """
    Sanitiza input para prevenir injeção.
    
    Args:
        value: Valor a ser sanitizado
        
    Returns:
        Valor sanitizado
    """
    if isinstance(value, str):
        # Remove caracteres perigosos
        value = re.sub(r'[<>"\']', '', value)
        # Remove scripts e tags HTML
        value = re.sub(r'<script.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<[^>]+>', '', value)
    return value


def validate_string(value: Any, min_length: int = 0, max_length: Optional[int] = None) -> str:
    """
    Valida e sanitiza uma string.
    
    Args:
        value: Valor a validar
        min_length: Comprimento mínimo
        max_length: Comprimento máximo
        
    Returns:
        String validada
        
    Raises:
        ValueError: Se a validação falhar
    """
    if not isinstance(value, str):
        raise ValueError("Valor deve ser uma string")
    
    value = sanitize_input(value)
    
    if len(value) < min_length:
        raise ValueError(f"String deve ter pelo menos {min_length} caracteres")
    
    if max_length and len(value) > max_length:
        raise ValueError(f"String deve ter no máximo {max_length} caracteres")
    
    return value


def validate_id(id_value: Any) -> str:
    """
    Valida um ID.
    
    Args:
        id_value: ID a validar
        
    Returns:
        ID validado
        
    Raises:
        ValueError: Se o ID for inválido
    """
    id_str = validate_string(id_value, min_length=1, max_length=100)
    
    # IDs devem conter apenas letras, números, hífens e underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', id_str):
        raise ValueError("ID contém caracteres inválidos")
    
    return id_str


def validate_dict(value: Any, required_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    Valida um dicionário.
    
    Args:
        value: Valor a validar
        required_keys: Chaves obrigatórias
        
    Returns:
        Dicionário validado
        
    Raises:
        ValueError: Se a validação falhar
    """
    if not isinstance(value, dict):
        raise ValueError("Valor deve ser um dicionário")
    
    if required_keys:
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise ValueError(f"Chaves obrigatórias ausentes: {', '.join(missing_keys)}")
    
    # Sanitiza valores do dicionário
    return {k: sanitize_input(v) for k, v in value.items()}

