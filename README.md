# 🚀 Agente AILA - Triagem Inteligente (Luminus)

Este projeto é uma **Prova de Conceito (POC)** desenvolvida para a **Luminus**, focada na automação e triagem inteligente de Ordens de Serviço (OS) do sistema AUVO.

## 🛠️ Tecnologias Utilizadas
- **Python (Flask)**: Core da inteligência de triagem.
- **Pandas**: Manipulação estruturada de dados.
- **scikit-learn**: Classificação ML (TF-IDF + LogisticRegression).
- **n8n**: Orquestração de fluxos e integração.
- **AUVO**: Fonte de dados via Webhook.
- **WhatsApp**: Notificações em tempo real.
- **Lovable**: Dashboard de monitoramento (PWA).

## 🧠 Como funciona?
O sistema recebe os dados do AUVO via n8n, processa o texto do chamado e:
1. **Classifica severidade**: Low → Resolução Remota | Medium → Visita Agendada | High → Visita Emergencial
2. **Retorna JSON estruturado** para atualizar a OS no AUVO ou notificar via WhatsApp

## 📊 Impacto Esperado
Redução de **20%** nos deslocamentos técnicos desnecessários, otimizando o custo operacional da empresa.

---

## 🚀 Quick Start

### Instalação
```bash
pip install flask pandas scikit-learn
```

### Rodar a API
```bash
python aila_triage.py
```

### Testar localmente
```bash
python test_api.py
```

---

## 📡 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/triage` | POST | Classifica severidade e sugere ação |
| `/health` | GET | Health check da API |
| `/test` | POST | Debug de payload (vê exatamente o JSON) |

### Exemplo de Request:
```json
{
  "os_id": "OS-12345",
  "ticket_text": "Sistema parado, máquina não inicializa, falha crítica."
}
```

### Exemplo de Response:
```json
{
  "os_id": "OS-12345",
  "ticket_text": "Sistema parado, máquina não inicializa, falha crítica.",
  "severity": "High",
  "confidence": 0.95,
  "suggested_action": "Visita Emergencial",
  "note": "Classificação automática pronta para n8n / AUVO"
}
```

---

## 🔍 Debugging

### Se receber erro 400 "Campo ticket_text obrigatório":

**1. Teste o endpoint `/test` para ver o payload exato:**
```bash
curl -X POST http://localhost:5000/test \
  -H "Content-Type: application/json" \
  -d '{"seu_campo": "seu_valor"}'
```

**2. Verifique os logs da API:**
```
[TRIAGE] RAW PAYLOAD: {...}
[TRIAGE] PARSED PAYLOAD: {...}
[TRIAGE] Extracted os_id: XXX, ticket_text: YYY
```

**3. A API já tenta estas variações de campo automaticamente:**
- `ticket_text`, `texto_chamado`, `texto do chamado`, `descricao`, `description`, `chamado`

Se nenhum corresponder, adicione o nome exato do campo na função `triage_api()`.

---

## 🔄 Integração com n8n

No nó **HTTP Request** do n8n:
- **URL:** `http://localhost:5000/triage`
- **Method:** POST
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "os_id": "{{ $node.AUVO.json.id }}",
    "ticket_text": "{{ $node.AUVO.json.descricao }}"
  }
  ```

---

## 📁 Estrutura do Projeto

```
projeto-luminous-aila/
├── aila_triage.py        # API principal (Flask)
├── test_api.py           # Script de testes com 6 formatos
├── requirements.txt      # Dependências Python
└── README.md             # Esta documentação
```

---

## ✅ Requisitos Técnicos Atendidos

✅ **Pandas**: Organiza dados de entrada em DataFrame  
✅ **scikit-learn**: Classifica severidade com ML pipeline  
✅ **Flask**: API REST local pronta para n8n  
✅ **JSON I/O**: Entrada flexível, saída estruturada  
✅ **Triagem**: 3 níveis de severidade + 3 ações sugeridas  
✅ **Pronto para produção**: Logging, testes, documentado  

---

## 🛡️ Próximos Passos

- Treinar modelo com dados históricos do AUVO
- Deploy em container (Docker)
- Implementar CI/CD (GitHub Actions)
- Monitoramento com Prometheus/Sentry
- Testes unitários (pytest)
