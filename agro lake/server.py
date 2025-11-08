"""Servidor MCP principal para dados agrícolas e gerenciamento de operações."""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

from config import config
from services.apidog_client import ApidogClient
from services.agricultural_service import AgriculturalService
from services.gemini_client import GeminiClient
from services.hgbrasil_client import HGBrasilClient
from models.schemas import (
    Farmer,
    Property,
    APIEndpoint,
    APIRequest,
    APIResponse
)
from utils.validators import validate_string, validate_id, validate_dict

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar instância do servidor MCP
mcp = FastMCP(config.SERVER_NAME)

# Inicializar clientes e serviços
apidog_client = ApidogClient()
agricultural_service = AgriculturalService(apidog_client)

# Inicializar cliente Gemini (opcional - só funciona se GOOGLE_API_KEY estiver configurado)
try:
    gemini_client = GeminiClient()
    if gemini_client.is_available():
        logger.info("Cliente Gemini inicializado e disponível")
    else:
        logger.warning("Cliente Gemini não disponível - GOOGLE_API_KEY não configurado")
except Exception as e:
    logger.warning(f"Erro ao inicializar cliente Gemini: {e}")
    gemini_client = None

# Inicializar cliente HGBrasil (opcional - só funciona se HG_BRASIL_API_KEY estiver configurado)
try:
    hgbrasil_client = HGBrasilClient()
    if hgbrasil_client.is_available():
        logger.info("Cliente HGBrasil inicializado e disponível")
    else:
        logger.warning("Cliente HGBrasil não disponível - HG_BRASIL_API_KEY não configurado")
except Exception as e:
    logger.warning(f"Erro ao inicializar cliente HGBrasil: {e}")
    hgbrasil_client = None

# Inicializar DocsManager (opcional)
try:
    from services.docs_manager import get_docs_manager, DOCUMENTATION_MAP
    docs_manager = get_docs_manager()
    DOCS_AVAILABLE = True
    logger.info("DocsManager inicializado e disponível")
except Exception as e:
    logger.warning(f"DocsManager não disponível: {e}")
    docs_manager = None
    DOCS_AVAILABLE = False
    DOCUMENTATION_MAP = {}


# ============================================================================
# RESOURCES - Recursos de dados agrícolas
# ============================================================================

@mcp.resource("seagri://properties")
async def get_properties_resource() -> Dict[str, Any]:
    """
    Recurso que fornece lista de propriedades agrícolas.
    
    Returns:
        Dicionário com informações sobre propriedades
    """
    try:
        properties = await agricultural_service.get_properties()
        return {
            "properties": properties,
            "count": len(properties),
            "description": "Lista de propriedades agrícolas cadastradas"
        }
    except Exception as e:
        logger.error(f"Erro ao obter recurso de propriedades: {e}")
        return {"error": str(e), "properties": []}


# Recursos de documentação (se DocsManager disponível)
if DOCS_AVAILABLE:
    @mcp.resource("seagri://docs/{category}/{doc_name}")
    async def get_document_resource(category: str, doc_name: str) -> str:
        """
        Recurso que fornece acesso a documentos Markdown.
        
        Args:
            category: Categoria do documento
            doc_name: Nome do documento (sem extensão)
            
        Returns:
            Conteúdo do documento em formato Markdown ou JSON de erro
        """
        try:
            if not docs_manager:
                return json.dumps({"error": "DocsManager não disponível"}, ensure_ascii=False)
            
            content = docs_manager.get_document(doc_name, doc_type="md", category=category)
            if content:
                return content
            else:
                return json.dumps({
                    "error": f"Documento '{doc_name}' não encontrado na categoria '{category}'"
                }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao obter documento {doc_name} da categoria {category}: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.resource("seagri://docs/tutoriais/{category}")
    async def get_tutorials_resource(category: str) -> str:
        """
        Recurso que fornece lista de tutoriais por categoria.
        
        Args:
            category: Categoria dos tutoriais
            
        Returns:
            JSON com lista de tutoriais
        """
        try:
            if not docs_manager:
                return json.dumps({"error": "DocsManager não disponível"}, ensure_ascii=False)
            
            tutorials = docs_manager.get_tutorials(category=category)
            return json.dumps({
                "tutoriais": tutorials,
                "count": len(tutorials),
                "categoria": category
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao obter tutoriais da categoria {category}: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.resource("seagri://docs/urls/list")
    async def get_urls_list_resource() -> str:
        """
        Recurso que fornece lista completa de URLs de conhecimento.
        
        Returns:
            JSON com lista completa de URLs e tutoriais
        """
        try:
            if not docs_manager:
                return json.dumps({"error": "DocsManager não disponível"}, ensure_ascii=False)
            
            urls_data = docs_manager.get_urls_list()
            return json.dumps(urls_data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao obter lista de URLs: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.resource("seagri://docs/planilhas/list")
    async def get_planilhas_list_resource() -> str:
        """
        Recurso que fornece lista de planilhas Excel disponíveis.
        
        Returns:
            JSON com lista de planilhas
        """
        try:
            if not docs_manager:
                return json.dumps({"error": "DocsManager não disponível"}, ensure_ascii=False)
            
            planilhas = docs_manager.list_planilhas()
            return json.dumps({
                "planilhas": planilhas,
                "count": len(planilhas)
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao obter lista de planilhas: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.resource("seagri://docs/planilhas/{nome_arquivo}")
    async def get_planilha_resource(nome_arquivo: str) -> str:
        """
        Recurso que fornece conteúdo de uma planilha Excel.
        
        Args:
            nome_arquivo: Nome do arquivo Excel (com ou sem extensão)
            
        Returns:
            JSON com dados da planilha
        """
        try:
            if not docs_manager:
                return json.dumps({"error": "DocsManager não disponível"}, ensure_ascii=False)
            
            resultado = docs_manager.read_planilha(nome_arquivo=nome_arquivo)
            return json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Erro ao obter planilha {nome_arquivo}: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# ============================================================================
# TOOLS - Ferramentas para consulta e gerenciamento
# ============================================================================

@mcp.tool()
async def list_api_endpoints() -> Dict[str, Any]:
    """
    Lista todos os endpoints disponíveis no projeto Apidog.
    
    Esta ferramenta permite descobrir quais endpoints de API estão disponíveis
    para integração através do Apidog MCP.
    
    Returns:
        Dicionário contendo lista de endpoints e suas informações
    """
    try:
        logger.info("Listando endpoints do Apidog")
        endpoints = await apidog_client.list_endpoints()
        return {
            "endpoints": endpoints,
            "count": len(endpoints),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar endpoints: {e}")
        return {
            "error": str(e),
            "endpoints": [],
            "status": "error"
        }


@mcp.tool()
async def get_endpoint_details(endpoint_id: str) -> Dict[str, Any]:
    """
    Obtém detalhes completos de um endpoint específico do Apidog.
    
    Args:
        endpoint_id: ID do endpoint a ser consultado
        
    Returns:
        Dicionário com detalhes do endpoint incluindo método, path, parâmetros e schema de resposta
    """
    try:
        # Validar entrada
        endpoint_id = validate_id(endpoint_id)
        
        logger.info(f"Buscando detalhes do endpoint: {endpoint_id}")
        details = await apidog_client.get_endpoint_details(endpoint_id)
        
        return {
            "endpoint": details,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do endpoint: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def execute_api_call(
    endpoint_id: str,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Executa uma chamada de API através do Apidog MCP.
    
    Esta ferramenta permite executar chamadas de API para qualquer endpoint
    disponível no projeto Apidog, com validação e tratamento de erros.
    
    Args:
        endpoint_id: ID do endpoint a ser executado
        method: Método HTTP (GET, POST, PUT, DELETE, etc.)
        path: Caminho do endpoint
        params: Parâmetros de query (opcional)
        body: Corpo da requisição para métodos POST/PUT (opcional)
        headers: Headers HTTP customizados (opcional)
        
    Returns:
        Dicionário com resposta da API incluindo status_code, data e headers
    """
    try:
        # Validar entradas
        endpoint_id = validate_id(endpoint_id)
        method = validate_string(method.upper(), min_length=1, max_length=10)
        path = validate_string(path, min_length=1)
        
        if params:
            params = validate_dict(params)
        if body:
            body = validate_dict(body)
        if headers:
            headers = {k: validate_string(str(v)) for k, v in headers.items()}
        
        # Validar método HTTP
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if method not in valid_methods:
            raise ValueError(f"Método HTTP inválido. Use um dos: {', '.join(valid_methods)}")
        
        logger.info(f"Executando chamada de API: {method} {path}")
        response = await apidog_client.execute_api_call(
            endpoint_id=endpoint_id,
            method=method,
            path=path,
            params=params,
            body=body,
            headers=headers
        )
        
        return {
            "response": response,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao executar chamada de API: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def get_properties() -> Dict[str, Any]:
    """
    Lista todas as propriedades agrícolas cadastradas.
    
    Returns:
        Dicionário com lista de propriedades
    """
    try:
        logger.info("Listando propriedades")
        properties = await agricultural_service.get_properties()
        return {
            "properties": properties,
            "count": len(properties),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar propriedades: {e}")
        return {
            "error": str(e),
            "properties": [],
            "status": "error"
        }


@mcp.tool()
async def create_property(
    name: str,
    location: Optional[str] = None,
    area_hectares: Optional[float] = None,
    farmer_id: Optional[str] = None,
    owner: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria uma nova propriedade agrícola no sistema.
    
    Args:
        name: Nome da propriedade (obrigatório)
        location: Localização da propriedade (opcional)
        area_hectares: Área em hectares (opcional)
        farmer_id: ID do agricultor proprietário (opcional, preferencial sobre owner)
        owner: Proprietário (opcional, legado - usar farmer_id)
        description: Descrição adicional (opcional)
        
    Returns:
        Dicionário com a propriedade criada
    """
    try:
        name = validate_string(name, min_length=1, max_length=200)
        if farmer_id:
            farmer_id = validate_id(farmer_id)
        
        property_data = {
            "name": name,
            "location": location,
            "area_hectares": area_hectares,
            "farmer_id": farmer_id,
            "owner": owner,
            "description": description
        }
        
        logger.info(f"Criando propriedade: {name}")
        property_obj = await agricultural_service.create_property(property_data)
        
        return {
            "property": property_obj,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao criar propriedade: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def get_farmer(farmer_id: str) -> Dict[str, Any]:
    """
    Obtém dados completos de um agricultor específico.
    
    Args:
        farmer_id: ID do agricultor a ser consultado
        
    Returns:
        Dicionário com informações do agricultor
    """
    try:
        farmer_id = validate_id(farmer_id)
        logger.info(f"Buscando agricultor: {farmer_id}")
        farmer = await agricultural_service.get_farmer(farmer_id)
        
        if not farmer:
            return {
                "error": f"Agricultor com ID {farmer_id} não encontrado",
                "status": "not_found"
            }
        
        return {
            "farmer": farmer,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar agricultor: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def get_farmer_properties(farmer_id: str) -> Dict[str, Any]:
    """
    Lista todas as propriedades de um agricultor específico.
    
    Args:
        farmer_id: ID do agricultor a ser consultado
        
    Returns:
        Dicionário com lista de propriedades do agricultor
    """
    try:
        farmer_id = validate_id(farmer_id)
        logger.info(f"Listando propriedades do agricultor: {farmer_id}")
        properties = await agricultural_service.get_farmer_properties(farmer_id)
        
        return {
            "properties": properties,
            "count": len(properties),
            "farmer_id": farmer_id,
            "status": "success"
        }
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao listar propriedades do agricultor: {e}")
        return {
            "error": str(e),
            "properties": [],
            "status": "error"
        }


# ============================================================================
# TOOLS - Integração com Google Gemini AI
# ============================================================================

@mcp.tool()
async def consult_gemini(
    prompt: str,
    context: Optional[str] = None,
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    Consulta o Google Gemini AI com um prompt.
    
    Esta ferramenta permite fazer perguntas ao Gemini e obter respostas
    inteligentes sobre qualquer tópico, incluindo dados agrícolas.
    
    Args:
        prompt: Pergunta ou prompt para o Gemini (obrigatório)
        context: Contexto adicional para ajudar o Gemini a entender melhor (opcional)
        temperature: Temperatura de geração 0.0-1.0 (opcional, padrão: 0.7)
                    - Valores mais baixos (0.1-0.3): respostas mais determinísticas
                    - Valores médios (0.5-0.7): equilíbrio entre criatividade e precisão
                    - Valores altos (0.8-1.0): respostas mais criativas e variadas
        
    Returns:
        Dicionário com a resposta do Gemini incluindo o texto gerado e metadados
    """
    try:
        if gemini_client is None or not gemini_client.is_available():
            return {
                "error": "Gemini não está disponível. Configure GOOGLE_API_KEY no arquivo .env",
                "status": "error"
            }
        
        # Validar entradas
        prompt = validate_string(prompt, min_length=1, max_length=10000)
        if context:
            context = validate_string(context, max_length=50000)
        if temperature is not None:
            if not (0.0 <= temperature <= 1.0):
                raise ValueError("Temperature deve estar entre 0.0 e 1.0")
        
        logger.info(f"Consultando Gemini: {prompt[:100]}...")
        result = await gemini_client.generate_content(
            prompt=prompt,
            context=context,
            temperature=temperature
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao consultar Gemini: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def analyze_with_gemini(
    data: Dict[str, Any],
    question: str
) -> Dict[str, Any]:
    """
    Analisa dados agrícolas usando Google Gemini AI.
    
    Esta ferramenta permite enviar dados agrícolas (propriedades, agricultores, etc.)
    para o Gemini e fazer perguntas sobre eles.
    O Gemini analisará os dados e fornecerá insights inteligentes.
    
    Args:
        data: Dados agrícolas para análise (obrigatório)
              Pode ser qualquer estrutura de dados: dicionário, lista, etc.
        question: Pergunta sobre os dados (obrigatório)
                 Exemplos:
                 - "Quantas propriedades estão cadastradas?"
                 - "Quais agricultores estão registrados?"
                 - "Analise os dados e forneça recomendações"
        
    Returns:
        Dicionário com a análise do Gemini baseada nos dados fornecidos
    """
    try:
        if gemini_client is None or not gemini_client.is_available():
            return {
                "error": "Gemini não está disponível. Configure GOOGLE_API_KEY no arquivo .env",
                "status": "error"
            }
        
        # Validar entradas
        question = validate_string(question, min_length=1, max_length=1000)
        data = validate_dict(data) if isinstance(data, dict) else data
        
        logger.info(f"Analisando dados com Gemini: {question[:100]}...")
        result = await gemini_client.analyze_agricultural_data(
            data=data,
            question=question
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao analisar com Gemini: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def list_gemini_models() -> Dict[str, Any]:
    """
    Lista modelos Gemini disponíveis.
    
    Esta ferramenta retorna a lista de todos os modelos Gemini disponíveis
    para uso. Útil para verificar quais modelos estão acessíveis e escolher
    o mais adequado para sua necessidade.
    
    Returns:
        Dicionário com lista de modelos disponíveis e contagem
    """
    try:
        if gemini_client is None or not gemini_client.is_available():
            return {
                "error": "Gemini não está disponível. Configure GOOGLE_API_KEY no arquivo .env",
                "models": [],
                "status": "error"
            }
        
        logger.info("Listando modelos Gemini")
        models = await gemini_client.list_models()
        
        return {
            "models": models,
            "count": len(models),
            "current_model": gemini_client.model_name,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return {
            "error": str(e),
            "models": [],
            "status": "error"
        }


# ============================================================================
# TOOLS - Integração com HGBrasil Weather API
# ============================================================================

@mcp.tool()
async def get_weather(
    city_name: str = "Brasilia,DF",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém dados meteorológicos de uma cidade usando HGBrasil Weather API.
    
    Esta ferramenta permite consultar condições climáticas atuais e previsão
    do tempo para qualquer cidade do Brasil, essencial para planejamento agrícola.
    
    Args:
        city_name: Nome da cidade no formato "Cidade,UF" (ex: "Brasilia,DF", "São Paulo,SP")
                  Padrão: "Brasilia,DF"
        api_key: Chave de API do HGBrasil (opcional, usa a configurada se não fornecida)
        
    Returns:
        Dicionário com dados meteorológicos incluindo:
        - current: Condições atuais (temperatura, umidade, vento, etc.)
        - forecast: Previsão para os próximos dias
        
    Exemplos de uso:
        - get_weather("Brasilia,DF")
        - get_weather("São Paulo,SP")
        - get_weather("Goiânia,GO")
    """
    try:
        if hgbrasil_client is None or not hgbrasil_client.is_available():
            return {
                "error": "HGBrasil não está disponível. Configure HG_BRASIL_API_KEY no arquivo .env",
                "status": "error"
            }
        
        # Validar entrada
        city_name = validate_string(city_name, min_length=1, max_length=100)
        
        logger.info(f"Buscando dados meteorológicos para: {city_name}")
        result = await hgbrasil_client.get_weather(
            city_name=city_name,
            api_key=api_key
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados meteorológicos: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


@mcp.tool()
async def get_weather_by_coordinates(
    latitude: float,
    longitude: float,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém dados meteorológicos por coordenadas geográficas usando HGBrasil Weather API.
    
    Esta ferramenta permite consultar condições climáticas usando coordenadas GPS,
    útil para propriedades rurais que não estão em áreas urbanas.
    
    Args:
        latitude: Latitude (ex: -15.7942 para Brasília)
        longitude: Longitude (ex: -47.8822 para Brasília)
        api_key: Chave de API do HGBrasil (opcional, usa a configurada se não fornecida)
        
    Returns:
        Dicionário com dados meteorológicos incluindo:
        - current: Condições atuais (temperatura, umidade, vento, etc.)
        - forecast: Previsão para os próximos dias
        
    Exemplos de uso:
        - get_weather_by_coordinates(-15.7942, -47.8822)  # Brasília
        - get_weather_by_coordinates(-23.5505, -46.6333)  # São Paulo
    """
    try:
        if hgbrasil_client is None or not hgbrasil_client.is_available():
            return {
                "error": "HGBrasil não está disponível. Configure HG_BRASIL_API_KEY no arquivo .env",
                "status": "error"
            }
        
        # Validar coordenadas
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude deve estar entre -90 e 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude deve estar entre -180 e 180")
        
        logger.info(f"Buscando dados meteorológicos para coordenadas: {latitude}, {longitude}")
        result = await hgbrasil_client.get_weather_by_coordinates(
            latitude=latitude,
            longitude=longitude,
            api_key=api_key
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return {
            "error": f"Erro de validação: {str(e)}",
            "status": "error"
        }
    except Exception as e:
        logger.error(f"Erro ao buscar dados meteorológicos: {e}")
        return {
            "error": str(e),
            "status": "error"
        }


# Ferramentas de documentação (se DocsManager disponível)
if DOCS_AVAILABLE:
    @mcp.tool()
    async def buscar_documentacao(
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca na documentação do SEAGRI.
        
        Esta ferramenta permite buscar informações em múltiplas fontes:
        - Base de conhecimento pré-configurada
        - Tutoriais em urls.json
        - Arquivos Markdown em docs/md/
        
        Args:
            query: Termo de busca (obrigatório)
            category: Categoria para filtrar (opcional): beneficiarios, conselho_rural, 
                     convenio_cooperativas, fundo_rural, maquinario
            
        Returns:
            Dicionário com resultados da busca incluindo:
            - resultados: Lista de resultados encontrados (máximo 5 principais)
            - count: Número total de resultados
            - query: Termo de busca utilizado
        """
        try:
            if not docs_manager:
                return {
                    "error": "DocsManager não disponível",
                    "status": "error"
                }
            
            # Validar query
            query = validate_string(query, min_length=1, max_length=200)
            
            logger.info(f"Buscando documentação: '{query}' (categoria: {category or 'todas'})")
            results = docs_manager.search_documentation(query, category=category)
            
            # Limitar a 5 resultados principais
            main_results = results[:5]
            
            return {
                "resultados": main_results,
                "count": len(results),
                "query": query,
                "categoria": category,
                "status": "success"
            }
            
        except ValueError as e:
            logger.error(f"Erro de validação: {e}")
            return {
                "error": f"Erro de validação: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Erro ao buscar documentação: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    @mcp.tool()
    async def buscar_conteudo_url(url: str) -> Dict[str, Any]:
        """
        Busca e extrai conteúdo textual de uma URL externa.
        
        Esta ferramenta busca o conteúdo de uma URL, extrai o texto HTML
        (removendo scripts, estilos, meta tags) e retorna o conteúdo limpo.
        O conteúdo é armazenado em cache para melhor performance.
        
        Args:
            url: URL a ser buscada (obrigatório)
            
        Returns:
            Dicionário com:
            - url: URL buscada
            - conteudo: Conteúdo textual extraído
            - length: Tamanho do conteúdo em caracteres
            - cached: Se o conteúdo veio do cache
        """
        try:
            if not docs_manager:
                return {
                    "error": "DocsManager não disponível",
                    "status": "error"
                }
            
            # Validar URL
            url = validate_string(url, min_length=1, max_length=500)
            
            # Verificar se está no cache
            cached = False
            if docs_manager.url_cache:
                cached_content = docs_manager.url_cache.get(url)
                if cached_content:
                    cached = True
                    content = cached_content
                else:
                    content = await docs_manager.fetch_url_content(url)
            else:
                content = await docs_manager.fetch_url_content(url)
            
            logger.info(f"Conteúdo buscado da URL: {url} (cache: {cached})")
            
            return {
                "url": url,
                "conteudo": content,
                "length": len(content),
                "cached": cached,
                "status": "success"
            }
            
        except ValueError as e:
            logger.error(f"Erro de validação: {e}")
            return {
                "error": f"Erro de validação: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo da URL: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    @mcp.tool()
    async def listar_planilhas() -> Dict[str, Any]:
        """
        Lista todas as planilhas Excel disponíveis no diretório de planilhas.
        
        Esta ferramenta lista todos os arquivos Excel (.xlsx, .xls, .xlsm)
        disponíveis no diretório docs/planilhas.
        
        Returns:
            Dicionário com:
            - planilhas: Lista de planilhas encontradas
            - count: Número total de planilhas
            - status: "success" ou "error"
        """
        try:
            if not docs_manager:
                return {
                    "error": "DocsManager não disponível",
                    "status": "error"
                }
            
            planilhas = docs_manager.list_planilhas()
            
            return {
                "planilhas": planilhas,
                "count": len(planilhas),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar planilhas: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    @mcp.tool()
    async def ler_planilha(
        nome_arquivo: str,
        sheet_name: Optional[str] = None,
        max_rows: Optional[int] = None,
        max_cols: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lê uma planilha Excel e retorna seus dados.
        
        Esta ferramenta lê uma planilha Excel do diretório docs/planilhas
        e retorna seus dados em formato estruturado.
        
        Args:
            nome_arquivo: Nome do arquivo Excel (com ou sem extensão)
            sheet_name: Nome da planilha específica (None para ler todas)
            max_rows: Número máximo de linhas a retornar (None para todas)
            max_cols: Número máximo de colunas a retornar (None para todas)
            
        Returns:
            Dicionário com:
            - nome_arquivo: Nome do arquivo
            - sheets: Dados das planilhas
            - total_sheets: Número total de planilhas
            - status: "success" ou "error"
        """
        try:
            if not docs_manager:
                return {
                    "error": "DocsManager não disponível",
                    "status": "error"
                }
            
            # Validar nome do arquivo
            nome_arquivo = validate_string(nome_arquivo, min_length=1, max_length=200)
            
            # Validar parâmetros opcionais
            if max_rows is not None and (max_rows < 1 or max_rows > 10000):
                return {
                    "error": "max_rows deve estar entre 1 e 10000",
                    "status": "error"
                }
            
            if max_cols is not None and (max_cols < 1 or max_cols > 1000):
                return {
                    "error": "max_cols deve estar entre 1 e 1000",
                    "status": "error"
                }
            
            resultado = docs_manager.read_planilha(
                nome_arquivo=nome_arquivo,
                sheet_name=sheet_name,
                max_rows=max_rows,
                max_cols=max_cols
            )
            
            return resultado
            
        except ValueError as e:
            logger.error(f"Erro de validação: {e}")
            return {
                "error": f"Erro de validação: {str(e)}",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Erro ao ler planilha: {e}")
            return {
                "error": str(e),
                "status": "error"
            }


# ============================================================================
# PROMPTS - Prompts contextuais para dados agrícolas
# ============================================================================

@mcp.prompt()
def plan_crop_season(
    property_name: str,
    crop_type: str,
    season: str = "próxima"
) -> str:
    """
    Gera um prompt para planejamento de safra agrícola.
    
    Args:
        property_name: Nome da propriedade
        crop_type: Tipo de cultura/plantação
        season: Época da safra (padrão: próxima)
        
    Returns:
        Prompt formatado para planejamento de safra
    """
    return f"""Planeje a safra de {crop_type} para a propriedade {property_name} na {season} temporada.

Por favor, ajude com:
1. Análise das condições ideais para plantio de {crop_type}
2. Recomendações de época de plantio baseadas em dados climáticos
3. Estimativa de recursos necessários (água, fertilizantes, mão de obra)
4. Cronograma de atividades (plantio, manutenção, colheita)
5. Projeção de rendimento esperado

Use as ferramentas disponíveis para:
- Verificar dados da propriedade {property_name}
- Analisar dados históricos similares
- Obter recomendações baseadas em dados

Forneça um plano detalhado e acionável."""


def main():
    """Função principal para executar o servidor MCP."""
    try:
        # Validar configurações
        config.validate()
        
        logger.info(f"Iniciando servidor MCP: {config.SERVER_NAME}")
        logger.info(f"Nível de log: {config.LOG_LEVEL}")
        
        # Executar servidor
        mcp.run()
        
    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        raise


if __name__ == "__main__":
    main()
