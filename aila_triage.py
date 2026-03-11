from flask import Flask, request, jsonify
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import NotFittedError

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
        ('tfidf', TfidfVectorizer(stop_words='portuguese')),
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


@app.route('/triage', methods=['POST'])
def triage_api():
    """Endpoint que recebe JSON do n8n e retorna classificação + ação."""
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({'error': 'Requisição sem JSON válido'}), 400

    # Aceita formatos diferentes; adequar ao n8n
    os_id = payload.get('os_id') or payload.get('OS_ID') or payload.get('id')
    ticket_text = payload.get('ticket_text') or payload.get('texto_chamado') or ''

    # Se o n8n enviar dados aninhados
    if not ticket_text and isinstance(payload.get('data'), dict):
        ticket_text = payload['data'].get('ticket_text', '') or payload['data'].get('texto_chamado', '')
        os_id = os_id or payload['data'].get('os_id') or payload['data'].get('id')

    # Falha se não houver texto
    if not ticket_text or not isinstance(ticket_text, str) or ticket_text.strip() == '':
        return jsonify({'error': 'Campo ticket_text (texto do chamado) é obrigatório'}), 400

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

    return jsonify(response), 200


if __name__ == '__main__':
    print('Iniciando AILA Triage (Flask) na porta 5000...')
    app.run(debug=True, host='0.0.0.0', port=5000)
