"""Cliente para integração com Apidog MCP."""

import logging
import httpx
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import config

logger = logging.getLogger(__name__)


class ApidogClient:
    """Cliente para interagir com Apidog MCP."""
    
    def __init__(self):
        """Inicializa o cliente Apidog."""
        self.base_url = config.APIDOG_BASE_URL
        self.access_token = config.APIDOG_ACCESS_TOKEN
        self.project_id = config.APIDOG_PROJECT_ID
        self.session: Optional[ClientSession] = None
        # Cliente HTTP para fazer requisições ao mock
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def connect(self) -> None:
        """Conecta ao servidor MCP do Apidog."""
        try:
            server_params = StdioServerParameters(
                command="cmd",
                args=[
                    "/c",
                    "npx",
                    "-y",
                    "apidog-mcp-server@latest",
                    f"--project-id={self.project_id}"
                ],
                env={
                    "APIDOG_ACCESS_TOKEN": self.access_token or ""
                }
            )
            
            # Nota: A conexão real com MCP seria feita aqui
            # Por enquanto, mantemos uma estrutura preparada para integração
            logger.info("Cliente Apidog inicializado")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao Apidog MCP: {e}")
            raise
    
    async def list_endpoints(self) -> List[Dict[str, Any]]:
        """
        Lista todos os endpoints disponíveis no projeto Apidog.
        
        Como o mock do Apifog não fornece uma API para listar endpoints,
        retornamos uma lista de endpoints conhecidos que podem ser usados.
        
        Returns:
            Lista de endpoints com suas informações
        """
        try:
            logger.info("Listando endpoints do Apidog")
            
            # Lista de endpoints conhecidos que podem ser usados com o mock
            # O usuário pode adicionar mais endpoints conforme necessário
            endpoints = [
                {
                    "id": "properties_get",
                    "name": "Obter Propriedade",
                    "method": "GET",
                    "path": "/api/properties/{id}",
                    "description": "Obtém detalhes de uma propriedade específica",
                    "parameters": [
                        {
                            "name": "id",
                            "type": "string",
                            "required": True,
                            "description": "ID da propriedade"
                        }
                    ],
                    "response_schema": {
                        "type": "object"
                    }
                },
                {
                    "id": "properties_list",
                    "name": "Listar Propriedades",
                    "method": "GET",
                    "path": "/api/properties",
                    "description": "Lista todas as propriedades agrícolas",
                    "parameters": [],
                    "response_schema": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                },
                {
                    "id": "farmer_get",
                    "name": "Obter dados do agricultor",
                    "method": "GET",
                    "path": "/api/farmers/{id}",
                    "description": "Obtém dados completos de um agricultor específico",
                    "parameters": [
                        {
                            "name": "id",
                            "type": "string",
                            "required": True,
                            "description": "ID do agricultor"
                        }
                    ],
                    "response_schema": {
                        "type": "object"
                    }
                },
                {
                    "id": "farmer_properties_list",
                    "name": "Listar propriedades do agricultor",
                    "method": "GET",
                    "path": "/api/farmers/{id}/properties",
                    "description": "Lista todas as propriedades de um agricultor específico",
                    "parameters": [
                        {
                            "name": "id",
                            "type": "string",
                            "required": True,
                            "description": "ID do agricultor"
                        }
                    ],
                    "response_schema": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            ]
            
            logger.info(f"Retornando {len(endpoints)} endpoints conhecidos")
            return endpoints
            
        except Exception as e:
            logger.error(f"Erro ao listar endpoints: {e}")
            raise
    
    async def get_endpoint_details(self, endpoint_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um endpoint específico.
        
        Args:
            endpoint_id: ID do endpoint
            
        Returns:
            Detalhes do endpoint
        """
        try:
            logger.info(f"Buscando detalhes do endpoint: {endpoint_id}")
            
            # Buscar o endpoint na lista de endpoints conhecidos
            endpoints = await self.list_endpoints()
            for endpoint in endpoints:
                if endpoint.get("id") == endpoint_id:
                    return endpoint
            
            # Se não encontrado, retornar estrutura básica
            return {
                "id": endpoint_id,
                "name": f"Endpoint {endpoint_id}",
                "method": "GET",
                "path": f"/api/{endpoint_id}",
                "description": f"Endpoint {endpoint_id}",
                "parameters": [],
                "response_schema": {}
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes do endpoint: {e}")
            raise
    
    async def execute_api_call(
        self,
        endpoint_id: str,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma chamada de API através do mock do Apidog.
        
        Args:
            endpoint_id: ID do endpoint
            method: Método HTTP
            path: Caminho do endpoint (ex: /api/cultures ou api/cultures)
            params: Parâmetros de query
            body: Corpo da requisição
            headers: Headers HTTP
            
        Returns:
            Resposta da API
        """
        try:
            # Normaliza a URL base (remove barra no final se existir)
            base_url = self.base_url.rstrip('/')
            
            # Remove a barra inicial do path se existir
            path = path.lstrip('/')
            
            # Constrói a URL completa usando o base_url do mock
            # Exemplo: http://127.0.0.1:3658/m1/1119125-1110256-default/api/properties
            url = f"{base_url}/{path}" if path else base_url
            
            # Prepara os headers
            request_headers = headers or {}
            if self.access_token:
                request_headers.setdefault("Authorization", f"Bearer {self.access_token}")
            request_headers.setdefault("Content-Type", "application/json")
            
            logger.info(f"Executando chamada de API ao mock: {method} {url}")
            
            # Faz a requisição HTTP ao mock
            response = await self.http_client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=body,
                headers=request_headers
            )
            
            response.raise_for_status()
            
            # Tenta fazer parse do JSON, se não conseguir retorna o texto
            try:
                response_data = response.json()
            except Exception:
                response_data = response.text
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers),
                "error": None
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao executar chamada de API: {e}")
            try:
                error_data = e.response.json() if e.response.content else {}
            except Exception:
                error_data = {"error": e.response.text if e.response.content else str(e)}
            
            return {
                "status_code": e.response.status_code,
                "data": error_data,
                "headers": dict(e.response.headers),
                "error": str(e)
            }
        except httpx.RequestError as e:
            logger.error(f"Erro de requisição ao executar chamada de API: {e}")
            return {
                "status_code": 0,
                "data": {},
                "headers": {},
                "error": f"Erro de conexão: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Erro ao executar chamada de API: {e}")
            raise
    
    async def get_openapi_spec(self) -> Dict[str, Any]:
        """
        Busca a especificação OpenAPI do projeto.
        
        Returns:
            Especificação OpenAPI
        """
        try:
            logger.info("Buscando especificação OpenAPI")
            
            # Exemplo de como seria a chamada via MCP:
            # result = await self.session.call_tool("get_openapi_spec", {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Erro ao buscar especificação OpenAPI: {e}")
            raise
    
    async def close(self) -> None:
        """Fecha a conexão com o servidor MCP."""
        if self.http_client:
            await self.http_client.aclose()
        if self.session:
            await self.session.close()
        logger.info("Conexão com Apidog MCP fechada")

