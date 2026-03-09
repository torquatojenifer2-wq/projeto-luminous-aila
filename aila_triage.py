from flask import Flask, request, jsonify

app = Flask(__name__)

def suggest_action(severity, orientation):
    """
    Sugere a ação baseada na severidade e no contexto do chamado.
    Foco: Reduzir visitas técnicas desnecessárias em 20%.
    """
    orientation = orientation.lower()
    
    if severity == 'High':
        return 'Visita Emergencial'
    
    # Identifica problemas que podem ser resolvidos remotamente
    remote_keywords = ['senha', 'configurar', 'resetar', 'acesso', 'software', 'login', 'ajuda']
    if any(kw in orientation for kw in remote_keywords) or severity == 'Low':
        return 'Resolução Remota'
    
    return 'Visita Agendada'

def process_triage(entities):
    """
    Processa a triagem usando lógica nativa do Python (sem Pandas/NumPy).
    """
    results = []
    urgent_keywords = ['urgente', 'emergencia', 'critico', 'falha', 'quebrado', 'parado']

    for task in entities:
        # Extração de dados com valores padrão
        priority = task.get('priority', 5)
        orientation = str(task.get('orientation', '')).lower()
        
        # Lógica de severidade
        if any(kw in orientation for kw in urgent_keywords) or priority <= 2:
            severity = 'High'
        elif priority == 3:
            severity = 'Medium'
        else:
            severity = 'Low'

        # Sugestão de ação
        action = suggest_action(severity, orientation)
        
        results.append({
            'taskID': task.get('taskID'),
            'severity': severity,
            'suggested_action': action,
            'orientation': orientation
        })
    
    return results

@app.route('/triage', methods=['POST'])
def triage():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        body = data.get('body', {})
        entities = body.get('entities', [])

        if not entities:
            return jsonify({'error': 'No entities found in payload'}), 400

        # Processamento
        processed_tasks = process_triage(entities)

        # Retorna o primeiro resultado para o n8n
        return jsonify(processed_tasks[0]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Iniciando Agente AILA na porta 5000...")
    app.run(debug=True, host='0.0.0.0', port=5000)