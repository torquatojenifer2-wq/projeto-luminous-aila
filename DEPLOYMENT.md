# 🚀 Deployment & Produção - AILA Triage

Guia para deployar a API AILA Triage em ambiente de produção.

---

## 🏗️ Opção 1: Deploy Local (Development)

### Passo 1: Instalar dependências

```bash
pip install flask pandas scikit-learn
```

### Passo 2: Rodar a API

```bash
python aila_triage.py
```

Saída esperada:
```
Iniciando AILA Triage (Flask) na porta 5000...
Endpoints disponíveis:
  POST /triage       - Classificação de tickets
  GET  /health       - Health check
  POST /test         - Debug de payload
 * Running on http://0.0.0.0:5000
```

### Validar

```bash
curl http://localhost:5000/health
```

---

## 📦 Opção 2: Deploy em Docker

### Passo 1: Criar arquivo `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar arquivos
COPY aila_triage.py .
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta
EXPOSE 5000

# Rodar aplicação
CMD ["python", "aila_triage.py"]
```

### Passo 2: Criar arquivo `docker-compose.yml`

```yaml
version: '3.8'

services:
  aila-triage:
    build: .
    container_name: aila-triage-api
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Passo 3: Build e rodar

```bash
# Build da imagem
docker build -t aila-triage:latest .

# Rodar container
docker run -p 5000:5000 aila-triage:latest

# Ou usar docker-compose
docker-compose up -d
```

### Validar

```bash
curl http://localhost:5000/health
```

---

## ☁️ Opção 3: Deploy em Servidor (Production Ready)

### Pré-requisitos

- Ubuntu/Linux 20.04+
- Python 3.9+
- Acesso SSH ao servidor

### Passo 1: Preparar servidor

```bash
# SSH no servidor
ssh user@seu-servidor.com

# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar Python + pip
sudo apt install -y python3 python3-pip python3-venv

# Instalar supervisor (para manter API rodando)
sudo apt install -y supervisor
```

### Passo 2: Deployar a aplicação

```bash
# Criar diretório
mkdir -p /home/user/aila-triage
cd /home/user/aila-triage

# Clonar ou copiar arquivos
# git clone https://github.com/seu-repo/projeto-luminous-aila.git .
# OU copiar arquivos manualmente

# Criar virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Passo 3: Configurar Supervisor

Criar arquivo `/etc/supervisor/conf.d/aila-triage.conf`:

```ini
[program:aila-triage]
directory=/home/user/aila-triage
command=/home/user/aila-triage/venv/bin/python aila_triage.py
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/user/aila-triage/logs/aila.log
user=user

[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/var/log/supervisor/supervisord.log

[group:aila]
programs=aila-triage
```

### Passo 4: Iniciar Supervisor

```bash
# Recarregar configuração
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar serviço
sudo supervisorctl start aila-triage

# Validar status
sudo supervisorctl status
```

### Passo 5: Configurar Nginx (Reverse Proxy)

Criar arquivo `/etc/nginx/sites-available/aila-triage`:

```nginx
server {
    listen 80;
    server_name aila.seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar site:

```bash
sudo ln -s /etc/nginx/sites-available/aila-triage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Passo 6: SSL/HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aila.seu-dominio.com
```

### Validar Deploy

```bash
curl https://aila.seu-dominio.com/health
```

---

## 🔒 Segurança em Produção

### 1. Desabilitar modo debug

Editar `aila_triage.py`:

```python
if __name__ == '__main__':
    # Em produção, usar Gunicorn ou similar
    # app.run(debug=False, host='127.0.0.1', port=5000)
    pass
```

### 2. Usar Gunicorn (melhor que Flask dev server)

```bash
pip install gunicorn

# Rodar com Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 aila_triage:app
```

### 3. Autenticação (opcional)

Se quiser proteger o endpoint:

```python
from functools import wraps

API_KEY = "sua-chave-secreta-aqui"

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Key')
        if token != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/triage', methods=['POST'])
@require_api_key
def triage_api():
    # ...
```

No n8n:
```
Headers:
  X-API-Key: sua-chave-secreta-aqui
```

### 4. Rate Limiting

```bash
pip install Flask-Limiter

from flask_limiter import Limiter

limiter = Limiter(
    app=app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/triage', methods=['POST'])
@limiter.limit("10 per minute")
def triage_api():
    # ...
```

---

## 📊 Monitoramento em Produção

### 1. Logs

```bash
# Ver logs em tempo real
sudo tail -f /home/user/aila-triage/logs/aila.log

# Ou com systemd
sudo journalctl -u aila-triage -f
```

### 2. Prometheus (Métricas)

```bash
pip install prometheus-flask-exporter

from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

Acessar: `http://localhost:5000/metrics`

### 3. Sentry (Error Tracking)

```bash
pip install sentry-sdk

import sentry_sdk
sentry_sdk.init("https://seu-sentry-dsn@sentry.io/project")
```

---

## 🔄 CI/CD com GitHub Actions

Criar arquivo `.github/workflows/deploy.yml`:

```yaml
name: Deploy AILA Triage

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pip install pytest
          pytest tests/
      
      - name: Deploy to server
        run: |
          # SSH e pull/restart
          ssh user@seu-servidor.com "cd /home/user/aila-triage && git pull origin main && source venv/bin/activate && pip install -r requirements.txt && supervisorctl restart aila-triage"
```

---

## ✅ Checklist de Deploy

**Pré-produção:**
- [ ] Testar localmente com `test_api.py`
- [ ] Testar com n8n real (staging)
- [ ] Revisar logs para erros
- [ ] Validar acurácia da classificação

**Deploy:**
- [ ] Escolher opção de hosting (Docker/Servidor/Cloud)
- [ ] Configurar banco de dados (se histórico)
- [ ] Configurar SSL/HTTPS
- [ ] Configurar monitoramento
- [ ] Documentar endpoint para equipe

**Pós-deploy:**
- [ ] Testar `/health` regularmente
- [ ] Monitorar logs de erro
- [ ] Treinar modelo com dados reais do AUVO
- [ ] Otimizar performance se necessário

---

## 🚨 Troubleshooting Deploy

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError` | Ativar virtual env: `source venv/bin/activate` |
| `Port 5000 in use` | Mudar porta ou encontrar processo: `lsof -i :5000` |
| `Connection refused n8n` | Verificar firewall, testar com `curl` local |
| `Memory leak` | Usar Gunicorn com `--max-requests` |
| `High latency` | Aumentar workers: `--workers 8` |

---

## 📞 Suporte

Para issues, verifique:
1. Logs de erro (`/var/log/supervisor/...`)
2. Status da API (`curl http://localhost:5000/health`)
3. Conexão com AUVO/n8n (testar com `/test`)
