# Seagri Server - MCP Server para Dados Agrícolas

Servidor MCP (Model Context Protocol) para consulta de dados agrícolas e gerenciamento de operações, com integração ao Apidog MCP e cliente GUI.

## Descrição

O Seagri Server é um servidor MCP robusto construído com FastMCP que permite:
- Consultar dados agrícolas (culturas, propriedades, operações, produtividade)
- Gerenciar operações agrícolas (plantio, colheita, irrigação, etc.)
- Integrar com todas as operações disponíveis no projeto Apidog
- Interagir através de uma interface gráfica moderna

## Características

- **Tools (Ferramentas)**: Ferramentas para consulta e gerenciamento de dados agrícolas
- **Resources (Recursos)**: Recursos de dados agrícolas acessíveis via URI
- **Prompts (Prompts)**: Prompts contextuais para planejamento e análise agrícola
- **Integração Apidog**: Acesso completo a todas as operações do projeto Apidog
- **Cliente GUI**: Interface gráfica moderna usando CustomTkinter
- **Validação Robusta**: Validação de dados usando Pydantic
- **Segurança**: Sanitização de inputs e tratamento de erros

## Instalação

### Pré-requisitos

- Python 3.13 ou superior
- pip ou uv para gerenciamento de dependências

### Passos de Instalação

1. Clone o repositório ou navegue até o diretório do projeto:
```bash
cd seagri-server
```

2. Instale as dependências:
```bash
pip install -e .
```

Ou usando uv:
```bash
uv pip install -e .
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- `APIDOG_ACCESS_TOKEN`: Seu token de acesso do Apidog
- `APIDOG_PROJECT_ID`: ID do seu projeto Apidog (padrão: 1119125)
- Outras configurações conforme necessário

## Configuração

### Configuração do MCP no Cursor

Adicione a seguinte configuração ao seu arquivo `mcp.json` (geralmente em `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "seagri-server": {
      "command": "python",
      "args": [
        "${workspaceFolder}/server.py"
      ],
      "env": {
        "APIDOG_ACCESS_TOKEN": "seu_token_aqui",
        "APIDOG_PROJECT_ID": "1119125",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Uso

### Servidor MCP

Execute o servidor MCP:

```bash
python server.py
```

Ou usando o script:
```bash
seagri-server
```

### Cliente GUI

Execute o cliente com interface gráfica:

```bash
python client.py
```

Ou usando o script:
```bash
seagri-client
```

## Tools Disponíveis

### Integração com Apidog

- **`list_api_endpoints()`**: Lista todos os endpoints disponíveis no projeto Apidog
- **`get_endpoint_details(endpoint_id)`**: Obtém detalhes de um endpoint específico
- **`execute_api_call(endpoint_id, method, path, params, body, headers)`**: Executa uma chamada de API

### Dados Agrícolas

- **`get_cultures()`**: Lista todas as culturas agrícolas
- **`get_culture(culture_id)`**: Obtém informações de uma cultura específica
- **`create_culture(name, ...)`**: Cria uma nova cultura agrícola
- **`get_properties()`**: Lista todas as propriedades agrícolas
- **`create_property(name, ...)`**: Cria uma nova propriedade agrícola
- **`get_operations(property_id, status)`**: Lista operações agrícolas com filtros
- **`create_operation(type, property_id, ...)`**: Cria uma nova operação agrícola
- **`get_productivity(property_id, culture_id, year)`**: Obtém dados de produtividade

## Resources Disponíveis

- **`seagri://cultures`**: Catálogo de culturas agrícolas disponíveis
- **`seagri://properties`**: Lista de propriedades agrícolas cadastradas
- **`seagri://operations`**: Catálogo de operações agrícolas disponíveis

## Prompts Disponíveis

- **`plan_crop_season(property_name, culture_name, season)`**: Gera prompt para planejamento de safra
- **`analyze_productivity(property_id, culture_id, year)`**: Gera prompt para análise de produtividade
- **`recommend_operations(property_id, current_season)`**: Gera prompt para recomendações de operações

## Como Acessar os Endpoints

**Importante**: O servidor MCP não expõe uma API HTTP tradicional. Os endpoints são acessados através de **tools** do MCP.

### URL Base Configurada

A URL base do Apidog está configurada como:
- **Padrão**: `https://api.apidog.com`
- **Configurável**: Defina `APIDOG_BASE_URL` no arquivo `.env`

### Acessando Endpoints

1. **Listar endpoints disponíveis**:
   ```python
   endpoints = list_api_endpoints()
   ```

2. **Obter detalhes de um endpoint**:
   ```python
   details = get_endpoint_details("endpoint_id")
   ```

3. **Executar chamada de API**:
   ```python
   response = execute_api_call(
       endpoint_id="endpoint_id",
       method="GET",
       path="/api/cultures",
       params={"limit": 10}
   )
   ```

Para mais detalhes, consulte `docs/ENDPOINTS.md`.

## Exemplos de Uso

### Exemplo 1: Listar Culturas

```python
# Usando o tool get_cultures
result = get_cultures()
print(result)
```

### Exemplo 2: Criar uma Operação

```python
# Criar uma operação de plantio
result = create_operation(
    type="plantio",
    property_id="prop_1",
    culture_id="cult_1",
    status="planned",
    notes="Plantio de soja na safra 2025"
)
print(result)
```

### Exemplo 3: Consultar Produtividade

```python
# Buscar dados de produtividade
result = get_productivity(
    property_id="prop_1",
    culture_id="cult_1",
    year=2024
)
print(result)
```

### Exemplo 4: Executar Chamada de API via Apidog

```python
# Executar uma chamada de API
result = execute_api_call(
    endpoint_id="endpoint_123",
    method="GET",
    path="/api/cultures",
    params={"limit": 10}
)
print(result)
```

## Estrutura do Projeto

```
seagri-server/
├── server.py              # Servidor MCP principal
├── client.py              # Cliente MCP com GUI
├── config.py              # Configurações e variáveis de ambiente
├── models/                # Modelos Pydantic para validação
│   └── schemas.py
├── services/              # Lógica de negócio e integração com APIs
│   ├── apidog_client.py
│   └── agricultural_service.py
├── gui/                   # Componentes de interface gráfica
│   ├── main_window.py
│   ├── widgets/
│   │   ├── tool_panel.py
│   │   ├── resource_viewer.py
│   │   └── prompt_builder.py
│   └── utils/
│       └── theme.py
├── utils/                 # Utilitários e helpers
│   └── validators.py
├── tests/                 # Testes unitários
├── .env.example           # Template de variáveis de ambiente
└── README.md              # Este arquivo
```

## Desenvolvimento

### Executar Testes

```bash
# Em desenvolvimento - adicionar testes conforme necessário
pytest tests/
```

### Logging

O servidor usa logging configurável. Configure o nível de log no arquivo `.env`:

```
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Segurança

- Todos os inputs são validados e sanitizados
- Credenciais são gerenciadas através de variáveis de ambiente
- Rate limiting pode ser configurado (desabilitado por padrão)
- Logs de operações sensíveis são registrados

## Contribuindo

Contribuições são bem-vindas! Por favor:
1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob licença MIT.

## Suporte

Para questões e suporte, abra uma issue no repositório do projeto.

## Changelog

### v0.1.0
- Implementação inicial do servidor MCP
- Integração com Apidog MCP
- Cliente GUI com CustomTkinter
- Tools, Resources e Prompts para dados agrícolas
- Validação de dados com Pydantic
- Tratamento robusto de erros

