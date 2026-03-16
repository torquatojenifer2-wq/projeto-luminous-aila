# Agente AILA

Triagem inteligente de chamados para operacoes tecnicas da Luminus Energia & Engenharia.

## Visao Geral

O **Agente AILA** e um MVP focado em automatizar a triagem inicial de Ordens de Servico (OS) vindas do AUVO.

Objetivo principal:
- Reduzir visitas tecnicas desnecessarias.
- Acelerar o tempo de resposta ao cliente.
- Apoiar o time operacional com recomendacoes automáticas.

A API recebe o texto do chamado, classifica a severidade e retorna uma sugestao de acao.

## Beneficios de Negocio

- Menos deslocamentos para casos resolviveis remotamente.
- Priorizacao rapida de chamados criticos.
- Padronizacao da triagem no fluxo operacional.
- Integracao simples com n8n e sistemas externos.

## Classificacao e Acao Sugerida

| Severidade | Acao sugerida |
|---|---|
| `Low` | `Resolucao Remota` |
| `Medium` | `Visita Agendada` |
| `High` | `Visita Emergencial` |

## Arquitetura (Resumo)

1. O chamado e aberto no AUVO.
2. O n8n captura a OS e envia os dados para a API AILA.
3. A API classifica a severidade com modelo de Machine Learning.
4. A resposta retorna para o fluxo de automacao (atualizacao de status, notificacoes, etc.).

## Stack Tecnologica

| Tecnologia | Uso no projeto |
|---|---|
| Python 3.11 | Linguagem principal |
| Flask | API HTTP |
| scikit-learn | Classificacao de severidade |
| pandas | Estruturacao e manipulacao dos dados |
| n8n | Orquestracao de automacoes |

## Estrutura do Projeto

```text
projeto-luminous-aila/
	aila_triage.py       # API Flask (endpoints /triage, /health, /test)
	train_model.py       # Script de treino/evolucao do modelo
	test_api.py          # Testes de payload para validar integracao
	sample_data.csv      # Dados de exemplo
	requirements.txt     # Dependencias Python
	DEPLOYMENT.md        # Guia de deploy local, Docker e servidor
	N8N_SETUP.md         # Guia de integracao com n8n
```

## Como Executar Localmente

### 1. Pre-requisitos

- Python 3.11+
- `pip`

### 2. Instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Subir a API

```bash
python aila_triage.py
```

API em:
- `http://localhost:5000`

## Endpoints

| Metodo | Endpoint | Descricao |
|---|---|---|
| `POST` | `/triage` | Classifica um chamado e sugere acao |
| `GET` ou `POST` | `/health` | Health check da aplicacao |
| `POST` | `/test` | Endpoint de debug para inspecionar payload |

## Exemplo de Uso

### Requisicao

```bash
curl -X POST http://localhost:5000/triage \
	-H "Content-Type: application/json" \
	-d '{
		"os_id": "OS-12345",
		"ticket_text": "Sistema parado, maquina nao inicializa."
	}'
```

### Resposta esperada

```json
{
	"os_id": "OS-12345",
	"ticket_text": "Sistema parado, maquina nao inicializa.",
	"severity": "High",
	"confidence": 0.93,
	"suggested_action": "Visita Emergencial",
	"note": "Classificacao automatica pronta para n8n / AUVO"
}
```

## Campos Aceitos no Payload

O endpoint `/triage` aceita multiplos formatos comuns no n8n.

Campos de texto aceitos:
- `ticket_text`
- `texto_chamado`
- `texto do chamado`
- `descricao` / `description`
- `chamado`, `mensagem`, `text`, `texto`

Campos de identificador aceitos:
- `os_id`
- `OS_ID`
- `id`
- `os`
- `ticket_id`

## Teste Rapido da API

Para validar varios formatos de payload:

```bash
python test_api.py
```

## Deploy

Para opcoes de deploy (local, Docker, servidor com Supervisor/Nginx), consulte:
- `DEPLOYMENT.md`

Para configuracao de automacao no n8n, consulte:
- `N8N_SETUP.md`

## Proximos Passos

- Treinar com base historica real de OS.
- Evoluir para NLP mais robusto.
- Adicionar observabilidade e metricas de acuracia.
- Criar dashboard de acompanhamento operacional.

## Autor

Projeto MVP de automacao inteligente para operacoes de campo.
