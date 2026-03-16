Write-Host "Iniciando stack completo..." -ForegroundColor Cyan
Write-Host ""

# 1. Inicia ngrok
Write-Host "Iniciando ngrok na porta 5678..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit","-Command","ngrok http 5678"

Start-Sleep -Seconds 2

# 2. Inicia n8n
Write-Host "Iniciando n8n..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit","-Command","`$env:WEBHOOK_URL='https://calmiest-wintrily-izaiah.ngrok-free.dev/'; n8n"

Start-Sleep -Seconds 2

# 3. Inicia Python
Write-Host "Iniciando aila_triage.py..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$PWD'; python C:\Users\Usuario\OneDrive\Desktop\projeto-luminous-aila\aila_triage.py"

Write-Host ""
Write-Host "Todos os servicos iniciados!" -ForegroundColor Green
Write-Host ""

Write-Host "Servicos:"
Write-Host "ngrok -> http://localhost:4040"
Write-Host "n8n -> http://localhost:5678"
Write-Host "aila_triage -> http://localhost:5000"