from flask import Flask, request, jsonify
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import NotFittedError
import json
import logging
import unicodedata

# Configurar logging para diagnosticar payloads
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SEVERITY_LEVEL = {'Baixa': 1, 'Média': 2, 'Alta': 3}

# Palavras-chave para regras de severidade em texto normalizado (sem acentos).
HIGH_HARD_KEYWORDS = {
    'incendio': 4,
    'fogo': 4,
    'chamas': 4,
    'explosao': 4,
    'vazamento de gas': 4,
    'choque eletrico': 4,
    'curto circuito': 3,
    'pessoa ferida': 5,
    'ferido': 4,
    'ferida': 4,
    'acidente': 4,
    'invasao': 4,
    'ransomware': 4,
    'acesso nao autorizado': 4,
}

HIGH_OPERATIONAL_KEYWORDS = {
    'perda total de dados': 4,
    'perda de dados': 3,
    'sistema fora do ar': 3,
    'parada total': 3,
    'indisponibilidade total': 3,
    'falha critica': 3,
    'ambiente inteiro indisponivel': 3,
    'risco imediato': 3,
}

MEDIUM_KEYWORDS = {
    'erro 500': 3,
    'erro 502': 3,
    'erro 503': 3,
    'timeout': 2,
    'instavel': 2,
    'intermitente': 2,
    'lentidao': 2,
    'lento': 2,
    'degradacao': 2,
    'degradada': 2,
    'travando': 2,
    'travado': 2,
    'nao abre': 2,
    'nao carrega': 2,
    'nao sincroniza': 2,
    'falhando': 2,
    'sem acesso': 2,
    'indisponivel': 2,
}

LOW_KEYWORDS = {
    'duvida': 2,
    'como': 1,
    'orientacao': 2,
    'documentacao': 2,
    'treinamento': 2,
    'ajuste': 2,
    'melhoria': 2,
    'solicitacao': 1,
    'senha': 2,
    'login': 2,
    'configurar': 2,
    'cadastro': 1,
    'icone': 1,
}

HIGH_MODIFIERS = {'urgente': 1, 'critico': 2, 'critica': 2, 'emergencia': 2}


def _normalize_text(text):
    if not isinstance(text, str):
        return ''
    lowered = text.strip().lower()
    normalized = unicodedata.normalize('NFKD', lowered)
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def _keyword_score(text, keyword_weights):
    score = 0
    matches = []
    for keyword, weight in keyword_weights.items():
        if keyword in text:
            score += weight
            matches.append(keyword)
    return score, matches


def _rule_based_severity(ticket_text):
    normalized = _normalize_text(ticket_text)
    if not normalized:
        return None, 0.0

    high_hard_score, high_hard_matches = _keyword_score(normalized, HIGH_HARD_KEYWORDS)
    high_operational_score, _ = _keyword_score(normalized, HIGH_OPERATIONAL_KEYWORDS)
    medium_score, medium_matches = _keyword_score(normalized, MEDIUM_KEYWORDS)
    low_score, low_matches = _keyword_score(normalized, LOW_KEYWORDS)
    high_modifier_score, _ = _keyword_score(normalized, HIGH_MODIFIERS)

    high_score = high_hard_score + high_operational_score + high_modifier_score

    # Se detectar risco físico/segurança explícito, sempre classifica como alta.
    if high_hard_matches:
        return 'Alta', 0.97

    if high_score >= 5 and high_score >= (medium_score + 2):
        return 'Alta', 0.90

    if medium_score >= 3 and medium_score >= (low_score + 1):
        return 'Média', 0.84

    if low_score >= 2 and high_score == 0 and medium_score <= 1 and low_matches:
        return 'Baixa', 0.89

    return None, 0.0


def _blend_predictions(rule_label, rule_confidence, model_label, model_confidence):
    if rule_label is None:
        return model_label, model_confidence

    if model_label is None:
        return rule_label, rule_confidence

    if rule_label == model_label:
        return rule_label, min(0.99, max(rule_confidence, model_confidence))

    if model_confidence < 0.60:
        return rule_label, max(rule_confidence, 0.72)

    rule_level = SEVERITY_LEVEL.get(rule_label, 2)
    model_level = SEVERITY_LEVEL.get(model_label, 2)

    if abs(rule_level - model_level) >= 2 and rule_confidence >= 0.85:
        return rule_label, rule_confidence

    if model_confidence >= 0.80:
        return model_label, model_confidence

    if rule_confidence >= (model_confidence + 0.08):
        return rule_label, rule_confidence

    return model_label, max(0.55, model_confidence * 0.92)

# Modelo de triagem (exemplo simples, pode adaptar para treino real em AUVO)
def build_severity_model():
    # Dataset sintético expandido para reduzir confusão entre baixa/média/alta.
    sample_data = [
        # ALTA - Emergências, riscos de segurança e indisponibilidade crítica
        ('Pegou fogo no ar-condicionado!!!', 'Alta'),
        ('Incêndio no equipamento, chamas visíveis', 'Alta'),
        ('Vazamento de gás, risco de explosão', 'Alta'),
        ('Pessoa ferida, chamada de emergência', 'Alta'),
        ('Sistema crítico parado, perda total de dados', 'Alta'),
        ('Máquina não inicializa, indisponibilidade total', 'Alta'),
        ('Falha crítica de equipamento, emergência', 'Alta'),
        ('Derramamento elétrico, risco imediato', 'Alta'),
        ('Falha de segurança, acesso não autorizado detectado', 'Alta'),
        ('Servidor principal fora do ar para toda operação', 'Alta'),
        ('Ataque detectado com possível invasão no ambiente', 'Alta'),
        ('Ransomware bloqueou arquivos da empresa', 'Alta'),
        ('Banco de dados corrompido com perda de dados', 'Alta'),
        ('Parada total no sistema de produção', 'Alta'),
        ('Explosão no nobreak durante operação', 'Alta'),
        ('Curto circuito em equipamento crítico', 'Alta'),
        
        # MÉDIA - Problemas operacionais significativos
        ('Erro 500 no dashboard, não consigo acessar', 'Média'),
        ('Relatório lento e com timeout intermitente', 'Média'),
        ('Conexão instável com servidor, queda esporádica', 'Média'),
        ('Performance degradada, respostas lentas', 'Média'),
        ('Sincronização com backup falhando', 'Média'),
        ('Aplicação travando ao salvar cadastro', 'Média'),
        ('Erro ao gerar relatório mensal', 'Média'),
        ('Sistema não carrega em alguns horários', 'Média'),
        ('API retornando erro 503 intermitente', 'Média'),
        ('Lentidão ao consultar pedidos no painel', 'Média'),
        ('Integração com ERP está falhando desde ontem', 'Média'),
        ('Usuários sem acesso ao módulo financeiro', 'Média'),
        ('Timeout ao sincronizar dados de clientes', 'Média'),
        ('Queda parcial no serviço de autenticação', 'Média'),
        
        # BAIXA - Dúvidas, ajustes, suporte administrativo
        ('Dúvida no uso da funcionalidade, orientação de senha', 'Baixa'),
        ('Solicitação de ajuste em layout de campo', 'Baixa'),
        ('Dúvida sobre procedimento de login', 'Baixa'),
        ('Como resetar minha senha?', 'Baixa'),
        ('Preciso de documentação sobre o recurso X', 'Baixa'),
        ('Solicitação de melhoria no nome do botão', 'Baixa'),
        ('Como configurar assinatura no sistema?', 'Baixa'),
        ('Ajuda para cadastrar um novo usuário', 'Baixa'),
        ('Pedido de treinamento para equipe nova', 'Baixa'),
        ('Ajustar ícone na tela inicial', 'Baixa'),
        ('Dúvida sobre regra de negócio no relatório', 'Baixa'),
        ('Solicito atualização de texto em campo informativo', 'Baixa'),
        ('Orientação para troca de senha de acesso', 'Baixa'),
        ('Pedido de documentação técnica atualizada', 'Baixa'),
    ]

    df = pd.DataFrame(sample_data, columns=['ticket_text', 'severity'])

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            strip_accents='unicode',
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )),
        ('clf', LogisticRegression(
            max_iter=1200,
            class_weight='balanced',
            random_state=42,
            C=2.0,
        ))
    ])

    pipeline.fit(df['ticket_text'], df['severity'])
    return pipeline

severity_model = build_severity_model()


def classify_severity(ticket_text):
    """Classifica severidade com abordagem hibrida (regras + sklearn)."""
    if not isinstance(ticket_text, str) or ticket_text.strip() == '':
        return 'Baixa', 0.0

    rule_label, rule_confidence = _rule_based_severity(ticket_text)

    model_label = None
    model_confidence = 0.0

    try:
        pred = severity_model.predict([ticket_text])[0]
        probs = severity_model.predict_proba([ticket_text])[0]
        model_label = pred
        model_confidence = float(max(probs))
    except NotFittedError:
        model_label = 'Média'
        model_confidence = 0.55

    final_label, final_confidence = _blend_predictions(
        rule_label,
        rule_confidence,
        model_label,
        model_confidence,
    )

    return final_label, final_confidence


def suggest_action(severity, ticket_text):
    """Sugere ação técnica de acordo com severidade e texto do chamado."""
    txt = _normalize_text(ticket_text)

    # Regras de triagem por severidade - PRIORITÁRIO
    if severity == 'Alta':
        # SEMPRE visita emergencial/imediata para casos críticos
        if any(kw in txt for kw in ['fogo', 'incendio', 'chamas', 'ferida', 'ferido', 'acidente', 'vazamento', 'explosao']):
            return 'Visita Emergencial Imediata'
        return 'Visita Emergencial'

    if severity == 'Média':
        # Sem possibilidade de resolução remota para incidentes operacionais
        if any(kw in txt for kw in ['parado', 'falha', 'indisponível', 'down', 'travado']):
            return 'Visita Técnica Agendada'
        return 'Suporte Técnico Remoto'

    # Severidade Baixa
    if any(k in txt for k in ['senha', 'login', 'configurar', 'acesso', 'como', 'dúvida', 'ajuda', 'documentação']):
        return 'Suporte Remoto (Chat / Telefone)'
    
    return 'Suporte Remoto'


def _get_field_from_payload(payload, keys):
    """Procura vários nomes de campo em payloads comuns do n8n."""
    if isinstance(payload, list):
        for item in payload:
            v = _get_field_from_payload(item, keys)
            if v not in [None, '']:
                return v
        return None

    if not isinstance(payload, dict):
        return None

    # procura primeira chave exata
    for key in keys:
        if key in payload and payload.get(key) not in [None, '']:
            return payload.get(key)

    # procura correspondência por substring para campos como 'texto do chamado'
    lower_keys = {k.lower(): v for k, v in payload.items()}
    for key in keys:
        normalized = key.replace('_', ' ').strip().lower()
        for candidate, value in lower_keys.items():
            if normalized == candidate or normalized in candidate or candidate in normalized:
                if value not in [None, '']:
                    return value

    # procura em dicionários aninhados (primeiro nível)
    for value in payload.values():
        if isinstance(value, (dict, list)):
            v = _get_field_from_payload(value, keys)
            if v not in [None, '']:
                return v

    return None


def _safe_json_parse(value):
    """Tenta converter string JSON em objeto Python sem lançar exceção."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _collect_possible_payloads(raw_data, parsed_json):
    """Monta uma lista de payloads candidatos em formatos comuns enviados pelo n8n."""
    candidates = []

    if parsed_json is not None:
        candidates.append(parsed_json)

    raw_json = _safe_json_parse(raw_data)
    if raw_json is not None:
        candidates.append(raw_json)

    if request.form:
        candidates.append(request.form.to_dict(flat=True))

    if request.values:
        candidates.append(request.values.to_dict(flat=True))

    # Expansao recursiva para suportar objetos/string JSON aninhados do n8n.
    expanded = []
    queue = list(candidates)

    while queue:
        candidate = queue.pop(0)
        expanded.append(candidate)

        if isinstance(candidate, dict):
            for value in candidate.values():
                if isinstance(value, (dict, list)):
                    queue.append(value)
                elif isinstance(value, str):
                    parsed_inner = _safe_json_parse(value)
                    if parsed_inner is not None:
                        queue.append(parsed_inner)

        if isinstance(candidate, list):
            for item in candidate:
                if isinstance(item, (dict, list)):
                    queue.append(item)
                elif isinstance(item, str):
                    parsed_item = _safe_json_parse(item)
                    if parsed_item is not None:
                        queue.append(parsed_item)

    return expanded


# Endpoint para receber do n8n
@app.route('/triage', methods=['POST'])
@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def triage_api(path=''):
    """Endpoint que recebe JSON do n8n e retorna classificação + ação."""
    # Log completo do payload para diagnosticar
    raw_data = request.get_data(as_text=True)
    logger.info(f"[TRIAGE] RAW PAYLOAD: {raw_data}")
    
    payload = request.get_json(force=True, silent=True)
    logger.info(f"[TRIAGE] PARSED PAYLOAD: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    payload_candidates = _collect_possible_payloads(raw_data, payload)
    logger.info(f"[TRIAGE] Payload candidates count: {len(payload_candidates)}")

    # Aceita formatos diferentes; adequar ao n8n
    os_id = None
    ticket_text = None
    text_keys = [
        'orientation',  # <--- ADICIONE ESTE (Campo principal do Auvo)
        'ticket_text',
        'texto_chamado',
        'ticket_text',
        'texto_chamado',
        'texto do chamado',
        'descricao',
        'description',
        'chamado',
        'mensagem',
        'text',
        'texto',
    ]
    id_keys = ['os_id', 'OS_ID', 'id', 'os', 'ticket_id']

    for candidate in payload_candidates:
        if not ticket_text:
            ticket_text = _get_field_from_payload(candidate, text_keys)
        if not os_id:
            os_id = _get_field_from_payload(candidate, id_keys)
        if ticket_text:
            break

    logger.info(f"[TRIAGE] Extracted os_id: {os_id}, ticket_text: {ticket_text}")

    # Fallback: parâmetros querystring por segurança
    if not ticket_text:
        ticket_text = request.args.get('ticket_text') or request.args.get('texto_chamado') or request.args.get('texto do chamado')

    if not ticket_text and request.form:
        ticket_text = (
            request.form.get('ticket_text')
            or request.form.get('texto_chamado')
            or request.form.get('texto do chamado')
            or request.form.get('description')
            or request.form.get('descricao')
        )

    if not os_id:
        os_id = request.args.get('os_id') or request.args.get('OS_ID') or request.args.get('id')

    if not os_id and request.form:
        os_id = request.form.get('os_id') or request.form.get('OS_ID') or request.form.get('id')

    # Falha se não houver texto
    if not ticket_text or not isinstance(ticket_text, str) or ticket_text.strip() == '':
        logger.error(f"[TRIAGE] ERRO: ticket_text não encontrado. Payload completo: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        return jsonify({'error': 'Campo ticket_text (texto do chamado) é obrigatório'}), 400

    logger.info(f"[TRIAGE] Processando: os_id={os_id}, ticket_text={ticket_text[:50]}...")

    # Normaliza e usa Panda para estruturar antes da lógica
    df = pd.DataFrame([{'os_id': os_id, 'ticket_text': ticket_text}])

    severity, confidence = classify_severity(df.loc[0, 'ticket_text'])
    action = suggest_action(severity, df.loc[0, 'ticket_text'])

    response = {
        'os_id': os_id,
        'ticket_text': df.loc[0, 'ticket_text'],
        'severity': severity,
        'confidence': round(confidence, 4),
        'suggested_action': action,
        'note': 'Classificação automática pronta para n8n / AUVO',
        'message_formatted': f"🚨 *ALERTA AILA: Triagem Concluída* 🚨\n\n*ID da Tarefa:* {os_id}\n*Gravidade:* {severity}\n*Ação Sugerida:* {action}"
    }

    logger.info(f"[TRIAGE] Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
    return jsonify(response), 200


@app.route('/health', methods=['GET', 'POST'])
def health():
    """Endpoint de health check / diagnóstico."""
    return jsonify({
        'status': 'ok',
        'service': 'AILA Triage',
        'version': '1.0',
        'available_endpoints': ['/triage', '/health', '/test'],
        'message': 'Use POST /triage com JSON contendo ticket_text'
    }), 200


@app.route('/test', methods=['POST'])
def test():
    """Endpoint de teste para validar formato de payload."""
    payload = request.get_json(force=True, silent=True)
    return jsonify({
        'received_payload': payload,
        'payload_type': str(type(payload)),
        'payload_keys': list(payload.keys()) if isinstance(payload, dict) else 'não é dict',
        'status': 'payload recebido com sucesso para análise'
    }), 200


if __name__ == '__main__':
    print('Iniciando AILA Triage (Flask) na porta 5000...')
    print('Endpoints disponíveis:')
    print('  POST /triage       - Classificação de tickets')
    print('  GET  /health       - Health check')
    print('  POST /test         - Debug de payload')
    app.run(debug=True, host='0.0.0.0', port=5000)