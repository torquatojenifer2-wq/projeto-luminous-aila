🚀 Agente AILA
Triagem Inteligente de Chamados – Luminus Energia & Engenharia










O Agente AILA é um Produto Mínimo Viável (MVP) desenvolvido para a Luminus Energia & Engenharia, com foco na automação da triagem de Ordens de Serviço (OS) provenientes do sistema AUVO.

O objetivo principal do projeto é reduzir em até 20% as visitas técnicas desnecessárias, utilizando Machine Learning para classificar automaticamente o nível de severidade dos chamados técnicos.

🧠 Objetivo do Projeto

Automatizar a análise inicial de chamados técnicos para:

⚡ Acelerar o tempo de resposta

💰 Reduzir custos operacionais

👨‍🔧 Evitar deslocamentos técnicos desnecessários

🤖 Implementar inteligência artificial no fluxo de atendimento

🛠️ Tecnologias Utilizadas
Tecnologia	Função
Python 3.11	Linguagem principal do projeto
Flask	API responsável pela triagem
Scikit-learn	Modelo de Machine Learning
Pandas	Processamento e manipulação de dados
Docker	Conteinerização da aplicação
Docker Compose	Orquestração dos serviços
n8n	Automação e integração com AUVO
Lovable	Interface PWA para monitoramento
🏗️ Arquitetura da Solução

A solução foi projetada seguindo a metodologia Top Hawks, priorizando escalabilidade, automação e impacto operacional.

Fluxo da Automação

1️⃣ Entrada
O chamado técnico é registrado no sistema AUVO.

2️⃣ Orquestração
O n8n detecta a nova Ordem de Serviço e envia o texto do chamado para o Agente AILA.

3️⃣ Inteligência Artificial
O agente processa o texto do chamado utilizando Machine Learning e classifica o nível de severidade:

Classificação	Ação
🟢 Low	Sugestão de resolução remota
🟡 Medium	Sugestão de visita agendada
🔴 High	Sugestão de visita emergencial

4️⃣ Saída

Após a classificação:

O n8n atualiza o status no AUVO

Envia notificação automática via WhatsApp

Registra a decisão no fluxo operacional

🚀 Como Executar o Projeto

Graças à conteinerização com Docker, o deploy do projeto é simples e rápido.

1️⃣ Pré-requisitos

Instale:

Docker Desktop

Docker Compose

2️⃣ Clone o repositório
git clone https://github.com/seu-repositorio/aila-agent.git
cd aila-agent
3️⃣ Execute o projeto
docker-compose up --build -d
4️⃣ API disponível em
http://localhost:5000/triage
📡 Endpoints da API
Método	Endpoint	Descrição
POST	/triage	Classifica um chamado
GET	/health	Verifica se a API está ativa
POST	/test	Endpoint de debug
📊 Impacto de Negócio
⏱️ Otimização de Tempo

Classificação automática de chamados diretamente no fluxo do AUVO.

💰 Redução de Custos

Menos deslocamentos técnicos para problemas resolvíveis remotamente.

🔒 Segurança Operacional

Uso de Docker garante reinicialização automática e isolamento do ambiente.

🔮 Próximas Evoluções

📈 Treinamento com mais dados reais de OS

🤖 Implementação de NLP avançado

📊 Dashboard analítico de chamados

🧠 Modelo de IA mais robusto

🔔 Sistema de alertas inteligentes

👨‍💻 Autor

Projeto desenvolvido como MVP de automação inteligente para operações técnicas.

Agente AILA – Automação + Inteligência Artificial para Operações de Campo
