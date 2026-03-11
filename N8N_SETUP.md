# 🔗 Configuração n8n → AILA Triage

Guia passo-a-passo para integrar seu workflow n8n com a API AILA Triage.

---

## ✅ Pré-requisitos

1. ✅ AILA Triage API rodando em `http://localhost:5000`
2. ✅ n8n rodando (local ou self-hosted)
3. ✅ Acesso aos dados do AUVO (webhook ou query)

---

## 🔧 Passo 1: Verificar o Formato do Payload

Antes de tudo, **identifique o nome exato dos campos** que o AUVO envia para o n8n.

### Método 1: Verificar no webhook AUVO → n8n

1. Abra seu workflow n8n que recebe dados do AUVO
2. Execute o workflow (ou simule uma OS)
3. Procure o nó que recebe do AUVO e **veja a estrutura exata do JSON**

Exemplo esperado:
```json
{
  "id": "OS-12345",              // ID da OS
  "descricao": "...",            // Texto do chamado
  "titulo": "...",               // Títulos
  "status": "aberto",
  "cliente": "..."
}
```

### Método 2: Usar o endpoint `/test` da API

Se não souber a estrutura exata:

1. Coloque um nó **HTTP Request** qualquer no n8n
2. Teste o endpoint `/test`:
   - **URL:** `http://localhost:5000/test`
   - **Method:** POST
   - **Body:** Copie/cole o JSON do AUVO

3. Veja a resposta com as chaves exatas

---

## 🛠️ Passo 2: Mapear Campos para AILA

Agora mapeie seus campos do AUVO para os que a AILA aceita:

| Campo AUVO | Campo AILA | Alternativas |
|-----------|----------|--------------|
| `id` ou `numero` | `os_id` | `OS_ID`, `os` |
| `descricao` ou `titulo` | `ticket_text` | `texto_chamado`, `texto do chamado`, `description` |

**Exemplo de mapeamento:**
- AUVO tem campo `descricao` → N8n deve enviar como `ticket_text`
- AUVO tem campo `id` → N8n deve enviar como `os_id`

---

## 📋 Passo 3: Criar o Nó HTTP Request no n8n

### Setup do Nó

1. **Adicione um nó novo: HTTP Request**
   - Click no `+` → search "HTTP Request" → selecione

2. **Configure o nó:**

| Campo | Valor |
|-------|-------|
| *Request Method* | POST |
| *URL* | `http://localhost:5000/triage` |
| *Authentication* | None (ou Basic se protegido) |

3. **Headers:**
   - Click em "Headers"
   - Adicione Header:
     - **Name:** `Content-Type`
     - **Value:** `application/json`

### Body (JSON)

Click em **Body** → selecione **JSON** mode

Insira (adaptando aos seus nomes de campo):

```json
{
  "os_id": "{{ $node.AUVO.json.id }}",
  "ticket_text": "{{ $node.AUVO.json.descricao }}"
}
```

**Se não souber o nome do nó anterior:**
- Veja qual nó traz dados do AUVO
- Substitua `AUVO` pelo nome real desse nó
- Use `.json.` para acessar campos

---

## 🔄 Passo 4: Processar a Resposta

A API retorna:

```json
{
  "os_id": "OS-12345",
  "severity": "High",
  "suggested_action": "Visita Emergencial",
  "confidence": 0.95,
  "ticket_text": "...",
  "note": "..."
}
```

### Opção A: Enviar para AUVO (atualizar OS)

```javascript
// Nó Function após HTTP Request da AILA
const result = $input.first().json;

return {
  "os_id": result.os_id,
  "severity": result.severity,
  "action": result.suggested_action,
  "confidence": result.confidence
};
```

Depois mapeie para um nó **AUVO REST API** (PUT/PATCH):

```
PUT /api/os/{os_id}
Body:
{
  "severity": "{{ $node['HTTP Request'].json.severity }}",
  "suggested_action": "{{ $node['HTTP Request'].json.suggested_action }}"
}
```

### Opção B: Enviar notificação WhatsApp

```javascript
// Nó WhatsApp após HTTP Request da AILA
const triage = $input.first().json;

// Crie uma mensagem estruturada
const mensagem = `
📋 *TRIAGEM AUTOMÁTICA - OS ${triage.os_id}*

🔴 *Severidade:* ${triage.severity}
📌 *Ação Sugerida:* ${triage.suggested_action}
💯 *Confiança:* ${(triage.confidence * 100).toFixed(0)}%

_Classificação automática pelo AILA_
`;

return {
  "message": mensagem,
  "phoneNumber": "5511999999999"
};
```

---

## 🧪 Passo 5: Teste Completo

### Teste Local (antes de usar no workflow)

```bash
curl -X POST http://localhost:5000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "os_id": "OS-12345",
    "ticket_text": "Sistema parado, falha crítica."
  }'
```

Deve retornar:
```json
{
  "severity": "High",
  "suggested_action": "Visita Emergencial",
  ...
}
```

### Teste no n8n

1. Crie um workflow simples:
   - **Nó 1 (Manual):** Clique para disparar
   - **Nó 2 (HTTP Request AILA):** Seu setup acima
   - **Nó 3 (Execute Workflow):** Mostre o resultado

2. Click "Execute Workflow"

3. Veja o output no Nó 2 (HTTP Request)

4. Se tudo OK, proceda para integração real

---

## 🐛 Troubleshooting

### ❌ "Campo ticket_text (texto do chamado) é obrigatório"

**Solução:**

1. Verifique o mapeamento de campos (Passo 2)
2. Use o endpoint `/test` para ver o JSON exato:
   ```bash
   curl -X POST http://localhost:5000/test \
     -H "Content-Type: application/json" \
     -d '{{ seu_payload_exato }}'
   ```
3. Adapte o `Body` do nó HTTP Request com o nome exato do campo

### ❌ "Connection refused" ou "ECONNREFUSED"

**Solução:**

1. Certifique-se que a API está rodando:
   ```bash
   python aila_triage.py
   ```
2. Teste o health check:
   ```bash
   curl http://localhost:5000/health
   ```
3. Se n8n está em Docker e API no host, use:
   - URL: `http://host.docker.internal:5000/triage` (Mac/Windows)
   - URL: `http://172.17.0.1:5000/triage` (Linux)

### ❌ "Invalid JSON"

**Solução:**

1. Verifique que o `Body` está em modo JSON
2. Certifique-se que `Content-Type: application/json` está nos Headers
3. Validar sintaxe do JSON (sem vírgulas extras, aspas corretas)

---

## 📊 Exemplo Workflow Completo

```
[Manual Trigger]
        ↓
[AUVO Query] → Obtém lista de OS abertas
        ↓
[HTTP Request → AILA Triage] → Classifica cada OS
        ↓
[Function] → Processa resultado
        ↓
[AUVO REST API] → Atualiza OS com severity
        ↓
[WhatsApp] → Notifica técnico se High/Medium
```

---

## ✅ Checklist Final

- [ ] API AILA rodando (`http://localhost:5000/health` retorna 200)
- [ ] Health check funciona: `curl http://localhost:5000/health`
- [ ] Identifiquei nomes exatos dos campos do AUVO
- [ ] Criei nó HTTP Request com URL correta
- [ ] Body JSON mapeia campos corretamente
- [ ] Testei localmente com `curl` → OK
- [ ] Testei no n8n com Manual Trigger → OK
- [ ] Pronto para integração em produção

---

## 💬 FAQs

**P: Posso chamar a API de um webhook n8n?**  
R: Sim, coloque o nó HTTP Request após receber o webhook do AUVO.

**P: E se o AUVO enviar múltiplas OS em um array?**  
R: Use um nó **Loop** antes do HTTP Request para iterar e chamar a AILA para cada OS.

**P: Posso armazenar o resultado historicamente?**  
R: Sim, adicione um nó **SQL** ou **Google Sheets** após processamento da AILA.

**P: Como melhorar a acurácia da classificação?**  
R: Treine o modelo (`aila_triage.py`) com dados históricos reais do AUVO.
