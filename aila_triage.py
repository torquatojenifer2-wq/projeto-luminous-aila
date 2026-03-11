from flask import Flask, request, jsonify
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import NotFittedError
import json
import logging

# Configurar logging para diagnosticar payloads
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Modelo de triagem (exemplo simples, pode adaptar para treino real em AUVO)
def build_severity_model():
    # Dataset de exemplo para demonstrar a pipeline
    sample_data = [
        ('Sistema parado, máquina não inicializa, indisponibilidade total', 'High'),
        ('Falha crítica de equipamento, emergência', 'High'),
        ('Erro 500 no dashboard, não consigo acessar', 'Medium'),
        ('Relatório lento e com timeout intermitente', 'Medium'),
        ('Dúvida no uso da funcionalidade, orientação de senha', 'Low'),
        ('Solicitação de ajuste em layout de campo', 'Low'),
    ]

    df = pd.DataFrame(sample_data, columns=['ticket_text', 'severity'])

    pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words=None)),
    ('clf', LogisticRegression(max_iter=300, random_state=42))
])

    pipeline.fit(df['ticket_text'], df['severity'])
    return pipeline

severity_model = build_severity_model()


def classify_severity(ticket_text):
    """Classifica severidade do ticket usando sklearn + pandas."""
    if not isinstance(ticket_text, str) or ticket_text.strip() == '':
        return 'Low', 0.0

    try:
        pred = severity_model.predict([ticket_text])[0]
        probs = severity_model.predict_proba([ticket_text])[0]
        confidence = float(max(probs))
    except NotFittedError:
        # fallback rule-based
        low_kw = ['senha', 'icone', 'ajuda', 'configurar', 'documentação']
        high_kw = ['urgente', 'emergência', 'critico', 'parado', 'falha', 'interrompido']
        ticket_lower = ticket_text.lower()
        if any(w in ticket_lower for w in high_kw):
            pred = 'High'
        elif any(w in ticket_lower for w in low_kw):
            pred = 'Low'
        else:
            pred = 'Medium'
        confidence = 0.55

    return pred, confidence


def suggest_action(severity, ticket_text):
    """Sugere ação técnica de acordo com severidade e texto do chamado."""
    txt = ticket_text.lower() if isinstance(ticket_text, str) else ''

    # Regras de triagem
    if severity == 'High':
        return 'Visita Emergencial'

    if any(k in txt for k in ['senha', 'login', 'configurar', 'acesso', 'documentação', 'ajuda']):
        return 'Resolução Remota'

    if severity == 'Medium':
        return 'Visita Agendada'

    return 'Resolução Remota'


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


@app.route('/triage', methods=['POST'])
def triage_api():
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
        'note': 'Classificação automática pronta para n8n / AUVO'  # meta
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