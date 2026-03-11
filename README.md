# 🚀 Agente AILA - Triagem Inteligente (Luminus)

Este projeto é uma **Prova de Conceito (POC)** desenvolvida para a **Luminus**, focada na automação e triagem inteligente de Ordens de Serviço (OS) do sistema AUVO.

## 🛠️ Tecnologias Utilizadas
- **Python (Flask)**: Core da inteligência de triagem.
- **n8n**: Orquestração de fluxos e integração.
- **AUVO**: Fonte de dados via Webhook.
- **WhatsApp**: Notificações em tempo real.
- **Lovable**: Dashboard de monitoramento (PWA).

## 🧠 Como funciona?
O sistema recebe os dados do AUVO, processa a prioridade e o título da tarefa e decide:
1. **Visita Emergencial**: Alerta via WhatsApp (Severidade Alta).
2. **Resolução Remota**: Sugestão automática para casos simples (Severidade Baixa).

## 📊 Impacto Esperado
Redução de **20%** nos deslocamentos técnicos desnecessários, otimizando o custo operacional da empresa.
