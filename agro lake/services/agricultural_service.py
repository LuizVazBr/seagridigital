"""Serviço para operações agrícolas."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.schemas import (
    Farmer,
    Property
)
from services.apidog_client import ApidogClient

logger = logging.getLogger(__name__)


class AgriculturalService:
    """Serviço para gerenciar dados e operações agrícolas."""
    
    def __init__(self, apidog_client: ApidogClient):
        """
        Inicializa o serviço agrícola.
        
        Args:
            apidog_client: Cliente Apidog para integração com API
        """
        self.apidog_client = apidog_client
        # Em produção, isso seria um banco de dados
        self._properties: Dict[str, Property] = {}
    
    async def get_properties(self) -> List[Dict[str, Any]]:
        """
        Lista todas as propriedades.
        
        Sempre tenta buscar do mock do Apifog primeiro.
        Se o mock não estiver disponível, retorna lista vazia com warning.
        
        Returns:
            Lista de propriedades
        """
        try:
            logger.info("Listando propriedades")
            
            # Sempre tentar buscar do mock do Apifog primeiro
            try:
                logger.info("Buscando propriedades do mock do Apifog")
                response = await self.apidog_client.execute_api_call(
                    endpoint_id="properties_list",
                    method="GET",
                    path="/api/properties"
                )
                
                if response.get("status_code") == 200 and response.get("data"):
                    data = response.get("data", [])
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "properties" in data:
                        return data["properties"]
                    elif isinstance(data, dict) and "data" in data:
                        return data["data"] if isinstance(data["data"], list) else []
                    else:
                        logger.warning("Resposta do mock não contém dados válidos")
                        return []
                else:
                    logger.warning(f"Erro ao buscar do mock: {response.get('error', 'Unknown error')}")
                    return []
            except Exception as e:
                logger.warning(f"Erro ao buscar do mock do Apifog: {e}")
                return []
            
        except Exception as e:
            logger.error(f"Erro ao listar propriedades: {e}")
            raise
    
    async def get_property(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma propriedade específica.
        
        Sempre tenta buscar do mock do Apifog primeiro.
        Se o mock não estiver disponível, retorna None com warning.
        
        Args:
            property_id: ID da propriedade
            
        Returns:
            Dados da propriedade ou None se não encontrada
        """
        try:
            logger.info(f"Buscando propriedade: {property_id}")
            
            # Sempre tentar buscar do mock do Apifog primeiro
            try:
                logger.info(f"Buscando propriedade {property_id} do mock do Apifog")
                response = await self.apidog_client.execute_api_call(
                    endpoint_id="properties_get",
                    method="GET",
                    path=f"/api/properties/{property_id}"
                )
                
                if response.get("status_code") == 200 and response.get("data"):
                    data = response.get("data", {})
                    if isinstance(data, dict):
                        return data
                    else:
                        logger.warning(f"Resposta do mock não contém dados válidos para propriedade {property_id}")
                        return None
                else:
                    logger.warning(f"Erro ao buscar propriedade {property_id} do mock: {response.get('error', 'Unknown error')}")
                    return None
            except Exception as e:
                logger.warning(f"Erro ao buscar propriedade {property_id} do mock do Apifog: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar propriedade: {e}")
            raise
    
    async def create_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova propriedade.
        
        Args:
            property_data: Dados da propriedade
            
        Returns:
            Propriedade criada
        """
        try:
            logger.info(f"Criando propriedade: {property_data.get('name')}")
            prop = Property(**property_data)
            prop.id = f"prop_{len(self._properties) + 1}"
            prop.created_at = datetime.now()
            self._properties[prop.id] = prop
            return prop.model_dump()
        except Exception as e:
            logger.error(f"Erro ao criar propriedade: {e}")
            raise
    
    async def get_farmer(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de um agricultor específico.
        
        Sempre tenta buscar do mock do Apifog primeiro.
        Se o mock não estiver disponível, retorna None com warning.
        
        Args:
            farmer_id: ID do agricultor
            
        Returns:
            Dados do agricultor ou None se não encontrado
        """
        try:
            logger.info(f"Buscando agricultor: {farmer_id}")
            
            # Sempre tentar buscar do mock do Apifog primeiro
            try:
                logger.info(f"Buscando agricultor {farmer_id} do mock do Apifog")
                response = await self.apidog_client.execute_api_call(
                    endpoint_id="farmer_get",
                    method="GET",
                    path=f"/api/farmers/{farmer_id}"
                )
                
                if response.get("status_code") == 200 and response.get("data"):
                    data = response.get("data", {})
                    if isinstance(data, dict):
                        return data
                    else:
                        logger.warning(f"Resposta do mock não contém dados válidos para agricultor {farmer_id}")
                        return None
                else:
                    logger.warning(f"Erro ao buscar agricultor {farmer_id} do mock: {response.get('error', 'Unknown error')}")
                    return None
            except Exception as e:
                logger.warning(f"Erro ao buscar agricultor {farmer_id} do mock do Apifog: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar agricultor: {e}")
            raise
    
    async def get_farmer_properties(self, farmer_id: str) -> List[Dict[str, Any]]:
        """
        Lista todas as propriedades de um agricultor específico.
        
        Sempre tenta buscar do mock do Apifog primeiro.
        Se o mock não estiver disponível, retorna lista vazia com warning.
        
        Args:
            farmer_id: ID do agricultor
            
        Returns:
            Lista de propriedades do agricultor
        """
        try:
            logger.info(f"Listando propriedades do agricultor: {farmer_id}")
            
            # Sempre tentar buscar do mock do Apifog primeiro
            try:
                logger.info(f"Buscando propriedades do agricultor {farmer_id} do mock do Apifog")
                response = await self.apidog_client.execute_api_call(
                    endpoint_id="farmer_properties_list",
                    method="GET",
                    path=f"/api/farmers/{farmer_id}/properties"
                )
                
                if response.get("status_code") == 200 and response.get("data"):
                    data = response.get("data", [])
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "properties" in data:
                        return data["properties"]
                    elif isinstance(data, dict) and "data" in data:
                        return data["data"] if isinstance(data["data"], list) else []
                    else:
                        logger.warning(f"Resposta do mock não contém dados válidos para propriedades do agricultor {farmer_id}")
                        return []
                else:
                    logger.warning(f"Erro ao buscar propriedades do agricultor {farmer_id} do mock: {response.get('error', 'Unknown error')}")
                    # Fallback: buscar todas as propriedades e filtrar por farmer_id
                    try:
                        all_properties = await self.get_properties()
                        filtered = [prop for prop in all_properties if prop.get("farmer_id") == farmer_id or prop.get("owner") == farmer_id]
                        return filtered
                    except Exception:
                        return []
            except Exception as e:
                logger.warning(f"Erro ao buscar propriedades do agricultor {farmer_id} do mock do Apifog: {e}")
                # Fallback: buscar todas as propriedades e filtrar por farmer_id
                try:
                    all_properties = await self.get_properties()
                    filtered = [prop for prop in all_properties if prop.get("farmer_id") == farmer_id or prop.get("owner") == farmer_id]
                    return filtered
                except Exception:
                    return []
            
        except Exception as e:
            logger.error(f"Erro ao listar propriedades do agricultor: {e}")
            raise

