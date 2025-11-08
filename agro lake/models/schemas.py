"""Modelos Pydantic para validação de dados agrícolas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AgriculturalData(BaseModel):
    """Modelo base para dados agrícolas."""
    
    id: Optional[str] = None
    name: str = Field(..., description="Nome do item")
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Farmer(AgriculturalData):
    """Modelo para agricultor."""
    
    name: str = Field(..., description="Nome do agricultor")
    email: Optional[str] = Field(None, description="Email do agricultor")
    phone: Optional[str] = Field(None, description="Telefone do agricultor")
    cpf_cnpj: Optional[str] = Field(None, description="CPF ou CNPJ do agricultor")
    address: Optional[str] = Field(None, description="Endereço do agricultor")
    city: Optional[str] = Field(None, description="Cidade")
    state: Optional[str] = Field(None, description="Estado")
    zip_code: Optional[str] = Field(None, description="CEP")


class Property(AgriculturalData):
    """Modelo para propriedade agrícola."""
    
    name: str = Field(..., description="Nome da propriedade")
    location: Optional[str] = Field(None, description="Localização")
    area_hectares: Optional[float] = Field(None, description="Área em hectares")
    farmer_id: Optional[str] = Field(None, description="ID do agricultor proprietário")
    owner: Optional[str] = Field(None, description="Proprietário (legado - usar farmer_id)")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Coordenadas GPS")


class APIEndpoint(BaseModel):
    """Modelo para endpoint da API."""
    
    id: str = Field(..., description="ID do endpoint")
    name: str = Field(..., description="Nome do endpoint")
    method: str = Field(..., description="Método HTTP")
    path: str = Field(..., description="Caminho do endpoint")
    description: Optional[str] = Field(None, description="Descrição")
    parameters: Optional[List[Dict[str, Any]]] = Field(None, description="Parâmetros")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Schema de resposta")


class APIRequest(BaseModel):
    """Modelo para requisição de API."""
    
    endpoint_id: str = Field(..., description="ID do endpoint")
    method: str = Field(..., description="Método HTTP")
    path: str = Field(..., description="Caminho do endpoint")
    params: Optional[Dict[str, Any]] = Field(None, description="Parâmetros de query")
    body: Optional[Dict[str, Any]] = Field(None, description="Corpo da requisição")
    headers: Optional[Dict[str, str]] = Field(None, description="Headers HTTP")


class APIResponse(BaseModel):
    """Modelo para resposta de API."""
    
    status_code: int = Field(..., description="Código de status HTTP")
    data: Optional[Any] = Field(None, description="Dados da resposta")
    headers: Optional[Dict[str, str]] = Field(None, description="Headers da resposta")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")

