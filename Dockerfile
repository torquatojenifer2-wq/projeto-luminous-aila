# Usa uma imagem leve do Python
FROM python:3.11-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências e instala as bibliotecas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o seu código do projeto para dentro do container
COPY . .

# Expõe a porta que o Flask está usando
EXPOSE 5000

# Comando para iniciar o script automaticamente
CMD ["python", "aila_triage.py"]