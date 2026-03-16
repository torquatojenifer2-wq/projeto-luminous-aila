from aila_triage import classify_severity, suggest_action

test_cases = [
    'Pegou fogo no arcondicionado!!!!',
    'Vazamento de gás, risco de explosão',
    'Erro 500 no dashboard, não consigo acessar',
    'Sistema parado completamente, máquina indisponível',
    'Qual é a minha senha?',
    'Como faço login?',
]

print('=' * 80)
print(f'{"TICKET":<45} {"SEV":<10} {"AÇÃO":<25}')
print('=' * 80)
for ticket in test_cases:
    sev, conf = classify_severity(ticket)
    action = suggest_action(sev, ticket)
    display = ticket[:42] + '...' if len(ticket) > 45 else ticket
    print(f'{display:<45} {sev:<10} {action:<25}')
print('=' * 80)
