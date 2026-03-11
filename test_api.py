"""
Script de teste para validar diferentes formatos de payload
que podem ser enviados pelo n8n para a API /triage
"""
import requests
import json

BASE_URL = "http://localhost:5000"

test_cases = [
    {
        "name": "Formato simples direto",
        "payload": {
            "os_id": "OS-12345",
            "ticket_text": "Sistema parado, não inicializa, falha crítica."
        }
    },
    {
        "name": "Formato com texto do chamado",
        "payload": {
            "os_id": "OS-999",
            "texto_chamado": "Cliente sem acesso, urgência."
        }
    },
    {
        "name": "Formato com 'texto do chamado' (espaços)",
        "payload": {
            "id": "OS-555",
            "texto do chamado": "Falha intermitente no módulo de faturamento."
        }
    },
    {
        "name": "Formato aninhado (data)",
        "payload": {
            "data": {
                "os_id": "OS-777",
                "ticket_text": "Erro 500 no dashboard, não consigo acessar."
            }
        }
    },
    {
        "name": "Formato n8n padrão (lista com json)",
        "payload": [
            {
                "json": {
                    "os_id": "OS-888",
                    "ticket_text": "Relatório lento e com timeout intermitente."
                }
            }
        ]
    },
    {
        "name": "Formato com body/entities",
        "payload": {
            "body": {
                "entities": [
                    {
                        "os_id": "OS-111",
                        "ticket_text": "Dúvida no uso da funcionalidade, orientação de senha."
                    }
                ]
            }
        }
    },
]

def test_endpoint(endpoint, payload, name):
    """Testa um endpoint com um payload específico."""
    print(f"\n{'='*80}")
    print(f"Teste: {name}")
    print(f"{'='*80}")
    print(f"Payload enviado:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=5)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERRO: {e}")

def test_health():
    """Testa o endpoint health."""
    print(f"\n{'='*80}")
    print("Health Check")
    print(f"{'='*80}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == '__main__':
    print("Iniciando testes da API AILA Triage...")
    print(f"Base URL: {BASE_URL}")
    
    # Teste health
    test_health()
    
    # Testes de payload
    for test_case in test_cases:
        test_endpoint("/triage", test_case["payload"], test_case["name"])
    
    print(f"\n{'='*80}")
    print("Testes finalizados!")
    print(f"{'='*80}")
