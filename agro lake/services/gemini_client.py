"""Cliente para integração com Google Gemini AI."""

import logging
from typing import Dict, Any, Optional, List
import os

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from config import config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Cliente para interagir com Google Gemini AI."""
    
    def __init__(self):
        """Inicializa o cliente Gemini."""
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai não está instalado. "
                "Instale com: pip install google-generativeai"
            )
        
        self.api_key = config.GOOGLE_API_KEY
        if not self.api_key:
            logger.warning(
                "GOOGLE_API_KEY não configurado. "
                "As tools do Gemini não estarão disponíveis."
            )
            self.connected = False
            return
        
        self.model_name = config.GEMINI_MODEL_NAME
        self.temperature = config.GEMINI_TEMPERATURE
        self.max_output_tokens = config.GEMINI_MAX_OUTPUT_TOKENS
        self.model = None
        self.generation_config = None
        self.connected = False
        
    def connect(self) -> None:
        """Conecta à API do Gemini."""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY não configurado")
        
        try:
            genai.configure(api_key=self.api_key)
            
            self.generation_config = genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            )
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
            
            # Testa a conexão
            list(genai.list_models())
            self.connected = True
            logger.info(f"Conectado ao Google Gemini (modelo: {self.model_name})")
            
        except Exception as e:
            self.connected = False
            logger.error(f"Erro ao conectar ao Gemini: {e}")
            raise
    
    def is_available(self) -> bool:
        """Verifica se o Gemini está disponível."""
        return GEMINI_AVAILABLE and self.api_key is not None
    
    async def generate_content(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Gera conteúdo usando o Gemini.
        
        Args:
            prompt: Prompt para o Gemini
            context: Contexto adicional (opcional)
            system_instruction: Instrução de sistema (opcional)
            temperature: Temperatura de geração (opcional, sobrescreve config)
            
        Returns:
            Resposta do Gemini
        """
        if not self.is_available():
            return {
                "error": "Gemini não está disponível. Configure GOOGLE_API_KEY.",
                "status": "error"
            }
        
        if not self.connected:
            self.connect()
        
        try:
            # Usar temperatura customizada se fornecida
            original_temp = self.temperature
            if temperature is not None:
                self.generation_config.temperature = temperature
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config
                )
            
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            
            if system_instruction:
                response = self.model.generate_content(
                    f"{system_instruction}\n\n{full_prompt}"
                )
            else:
                response = self.model.generate_content(full_prompt)
            
            # Restaurar temperatura original
            if temperature is not None:
                self.generation_config.temperature = original_temp
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config
                )
            
            return {
                "prompt": prompt,
                "response": response.text,
                "model": self.model_name,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def analyze_agricultural_data(
        self,
        data: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        """
        Analisa dados agrícolas usando Gemini.
        
        Args:
            data: Dados agrícolas
            question: Pergunta sobre os dados
            
        Returns:
            Análise do Gemini
        """
        if not self.is_available():
            return {
                "error": "Gemini não está disponível. Configure GOOGLE_API_KEY.",
                "status": "error"
            }
        
        system_instruction = """Você é um assistente especializado em dados agrícolas.
Analise os dados fornecidos e responda a pergunta do usuário de forma detalhada e útil.
Seja preciso e baseie suas respostas apenas nos dados fornecidos."""
        
        prompt = f"""DADOS AGRÍCOLAS:
{data}

PERGUNTA: {question}

Forneça uma resposta detalhada baseada nos dados fornecidos."""
        
        return await self.generate_content(
            prompt=prompt,
            system_instruction=system_instruction
        )
    
    async def list_models(self) -> List[str]:
        """Lista modelos Gemini disponíveis."""
        if not self.is_available():
            return []
        
        if not self.connected:
            self.connect()
        
        try:
            models = []
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    models.append(m.name)
            return models
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []

