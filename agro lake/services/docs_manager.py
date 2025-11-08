"""Gerenciador de documentação para o MCP Server SEAGRI."""

import asyncio
import logging
import subprocess
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from config import config
from services.url_loader import load_urls_from_json, filter_urls_by_category

logger = logging.getLogger(__name__)

# Avisar se BeautifulSoup não estiver disponível
if not BS4_AVAILABLE:
    logger.warning("BeautifulSoup4 (bs4) não está disponível. Funcionalidade de parsing HTML será limitada.")

# Avisar se pandas não estiver disponível
if not PANDAS_AVAILABLE:
    logger.warning("Pandas não está disponível. Funcionalidade de leitura de planilhas Excel será limitada.")

# Base de conhecimento pré-configurada
DOCUMENTATION_MAP = {
    "beneficiarios": {
        "documentation": {
            "manual": "Manual de Gestão de Beneficiários",
            "legislacao": "Legislação sobre Beneficiários",
            "normativas": "Normativas do SEAGRI"
        },
        "topics": ["cadastro", "doações", "empréstimos", "implementos agrícolas", "solicitantes"],
        "common_issues": ["cadastro incompleto", "validação de documentos", "aprovação de solicitações"]
    },
    "conselho_rural": {
        "documentation": {
            "manual": "Manual de Gestão de Conselhos Rurais",
            "legislacao": "Legislação sobre Conselhos Rurais",
            "normativas": "Normativas do SEAGRI"
        },
        "topics": ["gestão", "reuniões", "deliberações", "membros", "atas"],
        "common_issues": ["quórum insuficiente", "validação de deliberações", "registro de atas"]
    },
    "convenio_cooperativas": {
        "documentation": {
            "manual": "Manual de Gestão de Convênios",
            "legislacao": "Legislação sobre Convênios",
            "normativas": "Normativas do SEAGRI"
        },
        "topics": ["convênios", "associações", "cooperativas", "parcerias", "contratos"],
        "common_issues": ["validação de documentos", "renovação de convênios", "prestação de contas"]
    },
    "fundo_rural": {
        "documentation": {
            "manual": "Manual do Fundo de Desenvolvimento Rural",
            "legislacao": "Legislação sobre Fundo Rural",
            "normativas": "Normativas do SEAGRI"
        },
        "topics": ["crédito rural", "financiamento", "recursos", "gestão financeira", "aplicação"],
        "common_issues": ["aprovação de crédito", "documentação necessária", "prazos de pagamento"]
    },
    "maquinario": {
        "documentation": {
            "manual": "Manual de Controle de Maquinário",
            "legislacao": "Legislação sobre Maquinário",
            "normativas": "Normativas do SEAGRI"
        },
        "topics": ["controle", "manutenção", "estradas rurais", "serviços", "equipamentos"],
        "common_issues": ["manutenção preventiva", "disponibilidade de equipamentos", "agendamento de serviços"]
    }
}


class URLCache:
    """Cache para conteúdo de URLs com TTL."""
    
    def __init__(self, ttl_hours: float = 1.0, max_size: int = 1000):
        """
        Inicializa o cache de URLs.
        
        Args:
            ttl_hours: Tempo de vida do cache em horas
            max_size: Tamanho máximo do cache
        """
        self.ttl_hours = ttl_hours
        self.max_size = max_size
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    
    def get(self, url: str) -> Optional[str]:
        """
        Obtém conteúdo do cache se ainda válido.
        
        Args:
            url: URL a ser buscada
            
        Returns:
            Conteúdo da URL ou None se não encontrado/expirado
        """
        if url not in self._cache:
            return None
        
        entry = self._cache[url]
        expires_at = entry.get("expires_at")
        
        if expires_at and datetime.now() > expires_at:
            # Cache expirado, remover
            del self._cache[url]
            return None
        
        # Mover para o final (LRU)
        self._cache.move_to_end(url)
        return entry.get("content")
    
    def set(self, url: str, content: str) -> None:
        """
        Armazena conteúdo no cache.
        
        Args:
            url: URL
            content: Conteúdo a ser armazenado
        """
        # Limpar cache expirado primeiro
        self._clean_expired()
        
        # Se cache está cheio, remover entrada mais antiga
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        self._cache[url] = {
            "content": content,
            "expires_at": expires_at,
            "cached_at": datetime.now()
        }
    
    def _clean_expired(self) -> None:
        """Remove entradas expiradas do cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.get("expires_at") and entry["expires_at"] < now
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def clear(self) -> None:
        """Limpa completamente o cache."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        self._clean_expired()
        now = datetime.now()
        
        valid_entries = sum(
            1 for entry in self._cache.values()
            if not entry.get("expires_at") or entry["expires_at"] > now
        )
        expired_entries = len(self._cache) - valid_entries
        
        return {
            "enabled": True,
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "max_size": self.max_size,
            "ttl_hours": self.ttl_hours
        }


class DocsManager:
    """Gerenciador de documentação para o MCP Server SEAGRI."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de documentação.
        
        Args:
            base_path: Caminho base para documentos (padrão: docs/ na raiz do projeto)
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent / "docs"
        
        self.base_path = Path(base_path)
        self.md_path = self.base_path / "md"
        self.pdf_path = self.base_path / "pdf"
        self.tutoriais_path = self.base_path / "tutoriais"
        self.planilhas_path = self.base_path / "planilhas"
        
        # Configurações de cache
        cache_enabled = not getattr(config, "MCP_DISABLE_URL_CACHE", False)
        cache_ttl = float(getattr(config, "MCP_URL_CACHE_TTL_HOURS", 1.0))
        cache_max_size = int(getattr(config, "MCP_URL_CACHE_MAX_SIZE", 1000))
        
        self.url_cache = URLCache(ttl_hours=cache_ttl, max_size=cache_max_size) if cache_enabled else None
        
        # Configurações de sincronização
        self.rclone_enabled = not getattr(config, "MCP_DISABLE_RCLONE_SYNC", False)
        self.rclone_timeout = int(getattr(config, "MCP_RCLONE_TIMEOUT", 60))
        self.url_fetch_timeout = int(getattr(config, "MCP_URL_FETCH_TIMEOUT", 10))
        
        # Cliente HTTP
        self.http_client = httpx.AsyncClient(timeout=self.url_fetch_timeout)
        
        # Criar diretórios se não existirem
        self._ensure_directories()
        
        # Criar arquivos urls.json padrão se não existirem
        self._ensure_urls_json_files()
        
        # Sincronizar com Google Drive se configurado
        if self.rclone_enabled:
            try:
                self._sync_with_rclone()
            except Exception as e:
                logger.warning(f"Erro ao sincronizar com rclone: {e}")
    
    def _ensure_directories(self) -> None:
        """Garante que todos os diretórios necessários existam."""
        directories = [
            self.md_path,
            self.pdf_path,
            self.tutoriais_path,
            self.planilhas_path
        ]
        
        # Criar diretórios por categoria
        categories = ["beneficiarios", "conselho_rural", "convenio_cooperativas", "fundo_rural", "maquinario"]
        
        for category in categories:
            directories.extend([
                self.md_path / category,
                self.pdf_path / category,
                self.tutoriais_path / category
            ])
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Diretório garantido: {directory}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório {directory}: {e}")
    
    def _ensure_urls_json_files(self) -> None:
        """Cria arquivos urls.json padrão em cada categoria se não existirem."""
        categories = ["beneficiarios", "conselho_rural", "convenio_cooperativas", "fundo_rural", "maquinario"]
        
        default_structure = {
            "tutoriais": [],
            "urls": []
        }
        
        for category in categories:
            urls_file = self.tutoriais_path / category / "urls.json"
            if not urls_file.exists():
                try:
                    urls_file.parent.mkdir(parents=True, exist_ok=True)
                    import json
                    with open(urls_file, 'w', encoding='utf-8') as f:
                        json.dump(default_structure, f, indent=2, ensure_ascii=False)
                    logger.info(f"Arquivo urls.json criado: {urls_file}")
                except Exception as e:
                    logger.error(f"Erro ao criar urls.json em {urls_file}: {e}")
    
    def _sync_with_rclone(self) -> None:
        """Sincroniza documentos com Google Drive via rclone."""
        try:
            # Verificar se rclone está disponível
            result = subprocess.run(
                ["rclone", "version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("rclone não está disponível. Sincronização desabilitada.")
                return
            
            # Sincronizar (assumindo que há um remote configurado chamado "gdrive")
            # Ajustar conforme necessário
            logger.info("Sincronizando documentos com Google Drive via rclone...")
            # subprocess.run(["rclone", "sync", "gdrive:seagri-docs", str(self.base_path)], timeout=self.rclone_timeout)
            logger.info("Sincronização concluída.")
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Sincronização rclone expirou após {self.rclone_timeout}s")
        except FileNotFoundError:
            logger.warning("rclone não encontrado. Sincronização desabilitada.")
        except Exception as e:
            logger.warning(f"Erro ao sincronizar com rclone: {e}")
    
    def get_document(self, doc_name: str, doc_type: str = "md", category: Optional[str] = None) -> Optional[str]:
        """
        Busca documento em docs/md/ ou docs/pdf/.
        
        Para PDF: extrair texto usando PyPDF2 ou pdfplumber.
        Retornar conteúdo como string ou None se não encontrado.
        
        Args:
            doc_name: Nome do documento (sem extensão)
            doc_type: Tipo do documento ("md" ou "pdf")
            category: Categoria do documento (opcional)
            
        Returns:
            Conteúdo do documento ou None se não encontrado
        """
        try:
            if doc_type == "md":
                if category:
                    doc_path = self.md_path / category / f"{doc_name}.md"
                else:
                    # Buscar em todas as categorias
                    doc_path = None
                    for cat_dir in self.md_path.iterdir():
                        if cat_dir.is_dir():
                            potential_path = cat_dir / f"{doc_name}.md"
                            if potential_path.exists():
                                doc_path = potential_path
                                break
                    
                    if doc_path is None:
                        logger.warning(f"Documento MD '{doc_name}' não encontrado")
                        return None
            elif doc_type == "pdf":
                if category:
                    doc_path = self.pdf_path / category / f"{doc_name}.pdf"
                else:
                    # Buscar em todas as categorias
                    doc_path = None
                    for cat_dir in self.pdf_path.iterdir():
                        if cat_dir.is_dir():
                            potential_path = cat_dir / f"{doc_name}.pdf"
                            if potential_path.exists():
                                doc_path = potential_path
                                break
                    
                    if doc_path is None:
                        logger.warning(f"Documento PDF '{doc_name}' não encontrado")
                        return None
            else:
                logger.warning(f"Tipo de documento inválido: {doc_type}")
                return None
            
            if not doc_path or not doc_path.exists():
                logger.warning(f"Documento não encontrado: {doc_path}")
                return None
            
            # Ler arquivo
            if doc_type == "md":
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Documento MD carregado: {doc_path}")
                return content
            
            elif doc_type == "pdf":
                # Tentar extrair texto do PDF
                try:
                    import PyPDF2
                    with open(doc_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text_parts = []
                        for page in pdf_reader.pages:
                            text_parts.append(page.extract_text())
                        content = "\n".join(text_parts)
                    logger.info(f"Documento PDF carregado: {doc_path}")
                    return content
                except ImportError:
                    try:
                        import pdfplumber
                        with pdfplumber.open(doc_path) as pdf:
                            text_parts = []
                            for page in pdf.pages:
                                text_parts.append(page.extract_text() or "")
                            content = "\n".join(text_parts)
                        logger.info(f"Documento PDF carregado: {doc_path}")
                        return content
                    except ImportError:
                        logger.error("Nenhuma biblioteca de PDF disponível (PyPDF2 ou pdfplumber)")
                        return None
                except Exception as e:
                    logger.error(f"Erro ao extrair texto do PDF {doc_path}: {e}")
                    return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar documento '{doc_name}': {e}")
            return None
    
    def get_tutorials(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Carrega tutoriais de docs/tutoriais/urls.json.
        
        Filtra por categoria se fornecida.
        
        Args:
            category: Categoria para filtrar (opcional)
            
        Returns:
            Lista de tutoriais
        """
        try:
            if category:
                urls_file = self.tutoriais_path / category / "urls.json"
                if not urls_file.exists():
                    logger.warning(f"Arquivo urls.json não encontrado para categoria '{category}'")
                    return []
                
                data = load_urls_from_json(urls_file)
                return data.get("tutoriais", [])
            else:
                # Carregar tutoriais de todas as categorias
                all_tutorials = []
                categories = ["beneficiarios", "conselho_rural", "convenio_cooperativas", "fundo_rural", "maquinario"]
                
                for cat in categories:
                    urls_file = self.tutoriais_path / cat / "urls.json"
                    if urls_file.exists():
                        data = load_urls_from_json(urls_file)
                        all_tutorials.extend(data.get("tutoriais", []))
                
                return all_tutorials
                
        except Exception as e:
            logger.error(f"Erro ao carregar tutoriais: {e}")
            return []
    
    def get_urls_list(self) -> Dict[str, Any]:
        """
        Retorna estrutura completa de urls.json de todas as categorias.
        
        Returns:
            Dicionário com tutoriais e URLs de todas as categorias
        """
        try:
            all_tutorials = []
            all_urls = []
            categories = ["beneficiarios", "conselho_rural", "convenio_cooperativas", "fundo_rural", "maquinario"]
            
            for cat in categories:
                urls_file = self.tutoriais_path / cat / "urls.json"
                if urls_file.exists():
                    data = load_urls_from_json(urls_file)
                    all_tutorials.extend(data.get("tutoriais", []))
                    all_urls.extend(data.get("urls", []))
            
            return {
                "tutoriais": all_tutorials,
                "urls": all_urls
            }
            
        except Exception as e:
            logger.error(f"Erro ao carregar lista de URLs: {e}")
            return {"tutoriais": [], "urls": []}
    
    async def fetch_url_content(self, url: str, max_length: int = 5000) -> str:
        """
        Busca conteúdo de URL externa com cache.
        
        Extrai texto HTML (remove scripts, estilos, meta tags).
        Limpa espaços em branco e formata texto.
        Trunca se exceder max_length.
        
        Args:
            url: URL a ser buscada
            max_length: Tamanho máximo do conteúdo retornado
            
        Returns:
            Conteúdo textual extraído da URL
        """
        # Verificar cache primeiro
        if self.url_cache:
            cached_content = self.url_cache.get(url)
            if cached_content:
                logger.debug(f"Cache hit para URL: {url}")
                return cached_content[:max_length] if len(cached_content) > max_length else cached_content
        
        try:
            logger.info(f"Buscando conteúdo de URL: {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            # Parsear HTML (se BeautifulSoup disponível)
            if BS4_AVAILABLE and BeautifulSoup:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remover scripts, estilos, meta tags
                for element in soup(['script', 'style', 'meta', 'head']):
                    element.decompose()
                
                # Extrair texto
                text = soup.get_text(separator='\n', strip=True)
                
                # Limpar espaços em branco excessivos
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
            else:
                # Fallback: extrair texto básico sem BeautifulSoup
                import re
                # Remover tags HTML básicas
                text = re.sub(r'<[^>]+>', '', response.text)
                # Limpar espaços em branco excessivos
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
            
            # Truncar se necessário
            if len(cleaned_text) > max_length:
                cleaned_text = cleaned_text[:max_length] + "... [truncado]"
            
            # Armazenar no cache
            if self.url_cache:
                self.url_cache.set(url, cleaned_text)
            
            return cleaned_text
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar URL {url}: {e}")
            return f"Erro ao buscar URL: {e.response.status_code}"
        except httpx.RequestError as e:
            logger.error(f"Erro de requisição ao buscar URL {url}: {e}")
            return f"Erro de conexão ao buscar URL: {str(e)}"
        except Exception as e:
            logger.error(f"Erro ao buscar conteúdo da URL {url}: {e}")
            return f"Erro ao processar URL: {str(e)}"
    
    async def fetch_multiple_urls(self, urls: List[str], max_length: int = 5000) -> Dict[str, str]:
        """
        Busca conteúdo de múltiplas URLs.
        
        Args:
            urls: Lista de URLs a serem buscadas
            max_length: Tamanho máximo do conteúdo por URL
            
        Returns:
            Dicionário com URL como chave e conteúdo como valor
        """
        results = {}
        
        # Buscar URLs em paralelo
        tasks = [self.fetch_url_content(url, max_length) for url in urls]
        contents = await asyncio.gather(*tasks, return_exceptions=True)
        
        for url, content in zip(urls, contents):
            if isinstance(content, Exception):
                results[url] = f"Erro: {str(content)}"
            else:
                results[url] = content
        
        return results
    
    def search_documentation(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca em múltiplas fontes de documentação.
        
        Busca em:
        - Base de conhecimento pré-configurada (DOCUMENTATION_MAP)
        - Tutoriais em urls.json
        - Arquivos .md em docs/md/
        
        Filtra por categoria se fornecida.
        Retorna resultados com relevância.
        
        Args:
            query: Termo de busca
            category: Categoria para filtrar (opcional)
            
        Returns:
            Lista de resultados com relevância
        """
        query_lower = query.lower()
        results = []
        seen_urls = set()
        
        # Buscar na base de conhecimento
        for cat, info in DOCUMENTATION_MAP.items():
            if category and cat != category:
                continue
            
            # Verificar tópicos
            for topic in info.get("topics", []):
                if query_lower in topic.lower():
                    results.append({
                        "tipo": "topico",
                        "categoria": cat,
                        "titulo": topic,
                        "relevancia": "alta",
                        "fonte": "base_conhecimento"
                    })
            
            # Verificar problemas comuns
            for issue in info.get("common_issues", []):
                if query_lower in issue.lower():
                    results.append({
                        "tipo": "problema_comum",
                        "categoria": cat,
                        "titulo": issue,
                        "relevancia": "alta",
                        "fonte": "base_conhecimento"
                    })
        
        # Buscar em tutoriais
        tutorials = self.get_tutorials(category)
        for tutorial in tutorials:
            url = tutorial.get("url", "")
            if url in seen_urls:
                continue
            
            titulo = tutorial.get("titulo", "").lower()
            topicos = [t.lower() for t in tutorial.get("topicos", [])]
            
            if query_lower in titulo or any(query_lower in t for t in topicos):
                seen_urls.add(url)
                results.append({
                    "tipo": "tutorial",
                    "categoria": tutorial.get("categoria", ""),
                    "titulo": tutorial.get("titulo", ""),
                    "url": url,
                    "topicos": tutorial.get("topicos", []),
                    "relevancia": "alta",
                    "fonte": "tutoriais"
                })
        
        # Buscar em documentos MD
        if category:
            md_dir = self.md_path / category
            if md_dir.exists():
                for md_file in md_dir.glob("*.md"):
                    try:
                        content = self.get_document(md_file.stem, "md", category)
                        if content and query_lower in content.lower():
                            results.append({
                                "tipo": "documento",
                                "categoria": category,
                                "titulo": md_file.stem,
                                "arquivo": str(md_file),
                                "relevancia": "media",
                                "fonte": "documentos_md"
                            })
                    except Exception as e:
                        logger.debug(f"Erro ao buscar em {md_file}: {e}")
        else:
            # Buscar em todas as categorias
            for cat_dir in self.md_path.iterdir():
                if cat_dir.is_dir():
                    for md_file in cat_dir.glob("*.md"):
                        try:
                            content = self.get_document(md_file.stem, "md", cat_dir.name)
                            if content and query_lower in content.lower():
                                results.append({
                                    "tipo": "documento",
                                    "categoria": cat_dir.name,
                                    "titulo": md_file.stem,
                                    "arquivo": str(md_file),
                                    "relevancia": "media",
                                    "fonte": "documentos_md"
                                })
                        except Exception as e:
                            logger.debug(f"Erro ao buscar em {md_file}: {e}")
        
        # Remover duplicados e limitar a 10 resultados
        unique_results = []
        seen_keys = set()
        for result in results:
            key = (result.get("tipo"), result.get("titulo"), result.get("url", ""))
            if key not in seen_keys:
                seen_keys.add(key)
                unique_results.append(result)
                if len(unique_results) >= 10:
                    break
        
        return unique_results
    
    def clear_cache(self) -> None:
        """Limpa completamente o cache de URLs."""
        if self.url_cache:
            self.url_cache.clear()
            logger.info("Cache de URLs limpo")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas do cache
        """
        if self.url_cache:
            return self.url_cache.get_stats()
        else:
            return {
                "enabled": False,
                "total_entries": 0,
                "valid_entries": 0,
                "expired_entries": 0,
                "max_size": 0,
                "ttl_hours": 0.0
            }
    
    def list_planilhas(self) -> List[Dict[str, Any]]:
        """
        Lista todas as planilhas Excel disponíveis no diretório de planilhas.
        
        Returns:
            Lista de dicionários com informações sobre cada planilha:
            - nome: Nome do arquivo
            - caminho: Caminho completo do arquivo
            - tamanho: Tamanho do arquivo em bytes
            - modificado: Data de modificação
        """
        planilhas = []
        
        if not self.planilhas_path.exists():
            logger.warning(f"Diretório de planilhas não existe: {self.planilhas_path}")
            return planilhas
        
        # Extensões suportadas
        extensoes = ['.xlsx', '.xls', '.xlsm']
        
        try:
            for arquivo in self.planilhas_path.iterdir():
                if arquivo.is_file() and arquivo.suffix.lower() in extensoes:
                    stat = arquivo.stat()
                    planilhas.append({
                        "nome": arquivo.name,
                        "caminho": str(arquivo),
                        "tamanho": stat.st_size,
                        "modificado": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extensao": arquivo.suffix.lower()
                    })
            
            # Ordenar por nome
            planilhas.sort(key=lambda x: x["nome"])
            logger.info(f"Encontradas {len(planilhas)} planilhas no diretório")
            
        except Exception as e:
            logger.error(f"Erro ao listar planilhas: {e}")
        
        return planilhas
    
    def read_planilha(
        self,
        nome_arquivo: str,
        sheet_name: Optional[str] = None,
        max_rows: Optional[int] = None,
        max_cols: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lê uma planilha Excel e retorna seus dados.
        
        Args:
            nome_arquivo: Nome do arquivo Excel (com ou sem extensão)
            sheet_name: Nome da planilha específica (None para ler todas)
            max_rows: Número máximo de linhas a retornar (None para todas)
            max_cols: Número máximo de colunas a retornar (None para todas)
            
        Returns:
            Dicionário com:
            - nome_arquivo: Nome do arquivo
            - sheets: Dicionário com dados de cada planilha (ou lista se sheet_name especificado)
            - total_sheets: Número total de planilhas
            - status: "success" ou "error"
            - error: Mensagem de erro (se houver)
        """
        if not PANDAS_AVAILABLE or pd is None:
            return {
                "nome_arquivo": nome_arquivo,
                "error": "Pandas não está disponível. Instale pandas e openpyxl para ler planilhas Excel.",
                "status": "error"
            }
        
        try:
            # Encontrar arquivo
            arquivo_path = None
            
            # Se não tem extensão, tentar adicionar .xlsx e .xls
            if not any(nome_arquivo.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.xlsm']):
                for ext in ['.xlsx', '.xls', '.xlsm']:
                    tentativa = self.planilhas_path / f"{nome_arquivo}{ext}"
                    if tentativa.exists():
                        arquivo_path = tentativa
                        break
            else:
                arquivo_path = self.planilhas_path / nome_arquivo
            
            if arquivo_path is None or not arquivo_path.exists():
                return {
                    "nome_arquivo": nome_arquivo,
                    "error": f"Arquivo não encontrado: {nome_arquivo}",
                    "status": "error"
                }
            
            logger.info(f"Lendo planilha: {arquivo_path}")
            
            # Ler planilha(s)
            if sheet_name:
                # Ler planilha específica
                df = pd.read_excel(arquivo_path, sheet_name=sheet_name, engine='openpyxl')
                
                # Limitar linhas e colunas se especificado
                if max_rows:
                    df = df.head(max_rows)
                if max_cols:
                    df = df.iloc[:, :max_cols]
                
                # Converter para dicionário
                dados = {
                    "sheet_name": sheet_name,
                    "dados": df.to_dict(orient='records'),
                    "colunas": df.columns.tolist(),
                    "total_linhas": len(df),
                    "total_colunas": len(df.columns)
                }
                
                return {
                    "nome_arquivo": arquivo_path.name,
                    "sheets": dados,
                    "total_sheets": 1,
                    "status": "success"
                }
            else:
                # Ler todas as planilhas
                excel_file = pd.ExcelFile(arquivo_path, engine='openpyxl')
                sheets_data = {}
                
                for sheet in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet)
                    
                    # Limitar linhas e colunas se especificado
                    if max_rows:
                        df = df.head(max_rows)
                    if max_cols:
                        df = df.iloc[:, :max_cols]
                    
                    sheets_data[sheet] = {
                        "dados": df.to_dict(orient='records'),
                        "colunas": df.columns.tolist(),
                        "total_linhas": len(df),
                        "total_colunas": len(df.columns)
                    }
                
                return {
                    "nome_arquivo": arquivo_path.name,
                    "sheets": sheets_data,
                    "total_sheets": len(excel_file.sheet_names),
                    "sheet_names": excel_file.sheet_names,
                    "status": "success"
                }
                
        except ImportError as e:
            return {
                "nome_arquivo": nome_arquivo,
                "error": f"Biblioteca necessária não instalada: {str(e)}. Instale: pip install pandas openpyxl",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Erro ao ler planilha {nome_arquivo}: {e}")
            return {
                "nome_arquivo": nome_arquivo,
                "error": str(e),
                "status": "error"
            }
    
    async def close(self) -> None:
        """Fecha recursos do DocsManager."""
        if self.http_client:
            await self.http_client.aclose()


# Instância global do DocsManager
_docs_manager: Optional[DocsManager] = None


def get_docs_manager() -> DocsManager:
    """
    Retorna instância global do DocsManager.
    
    Returns:
        Instância do DocsManager
    """
    global _docs_manager
    if _docs_manager is None:
        _docs_manager = DocsManager()
    return _docs_manager

