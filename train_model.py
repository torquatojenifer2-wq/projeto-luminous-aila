"""
Script para treinar o modelo AILA Triage com dados históricos do AUVO.

Como usar:
    python train_model.py --data ./auvo_historico.csv --output ./modelo_treinado.pkl

Formato esperado do CSV:
    ticket_text,severity
    "Descrição do chamado 1", High
    "Descrição do chamado 2", Low
    ...
"""

import pandas as pd
import argparse
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np


def load_data(csv_path):
    """Carrega dados históricos do AUVO."""
    df = pd.read_csv(csv_path)
    
    # Validar colunas
    if 'ticket_text' not in df.columns or 'severity' not in df.columns:
        raise ValueError("CSV deve ter colunas 'ticket_text' e 'severity'")
    
    # Remover valores nulos
    df = df.dropna(subset=['ticket_text', 'severity'])
    
    print(f"✅ Dados carregados: {len(df)} registros")
    print(f"\nDistribuição de severidade:")
    print(df['severity'].value_counts())
    
    return df


def train_model(df):
    """Treina o modelo com os dados históricos."""
    X = df['ticket_text']
    y = df['severity']
    
    # Dividir em treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 Split: {len(X_train)} treino, {len(X_test)} teste")
    
    # Criar pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words='portuguese',
            min_df=2,
            max_df=0.8
        )),
        ('clf', LogisticRegression(
            max_iter=1000,
            random_state=42,
            multi_class='multinomial',
            solver='lbfgs'
        ))
    ])
    
    # Treinar
    print("\n🤖 Treinando modelo...")
    pipeline.fit(X_train, y_train)
    
    # Avaliar no conjunto de teste
    y_pred = pipeline.predict(X_test)
    score = pipeline.score(X_test, y_test)
    
    print(f"\n✅ Acurácia no teste: {score:.2%}")
    
    # Relatório detalhado
    print("\n📈 Classificação por classe:")
    print(classification_report(y_test, y_pred))
    
    print("\n🔄 Matriz de confusão:")
    print(confusion_matrix(y_test, y_pred))
    
    return pipeline


def test_model(pipeline):
    """Testa o modelo com exemplos de entrada."""
    test_cases = [
        "Sistema parado, máquina não inicializa, falha crítica.",
        "Dúvida sobre como usar a funcionalidade de senha.",
        "Relatório lento e com timeout intermitente.",
        "Erro 500 no dashboard, não consigo acessar.",
        "Cliente sem acesso ao sistema, urgência.",
    ]
    
    print("\n\n🧪 Exemplos de teste do modelo:")
    print("=" * 80)
    
    for text in test_cases:
        pred = pipeline.predict([text])[0]
        probs = pipeline.predict_proba([text])[0]
        confidence = max(probs)
        
        classes = pipeline.classes_
        prob_dict = {c: f"{p:.2%}" for c, p in zip(classes, probs)}
        
        print(f"\n📝 Texto: {text[:60]}...")
        print(f"🔴 Predição: {pred}")
        print(f"💯 Confiança: {confidence:.2%}")
        print(f"📊 Probabilidades: {prob_dict}")


def save_model(pipeline, output_path):
    """Salva o modelo treinado."""
    joblib.dump(pipeline, output_path)
    print(f"\n💾 Modelo salvo em: {output_path}")


def load_and_use_model(model_path):
    """Carrega modelo já trainado."""
    pipeline = joblib.load(model_path)
    print(f"✅ Modelo carregado de: {model_path}")
    return pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Treina modelo AILA Triage com dados históricos"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="sample_data.csv",
        help="Caminho para o arquivo CSV com dados históricos"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="modelo_aila.pkl",
        help="Caminho para salvar o modelo treinado"
    )
    
    args = parser.parse_args()
    
    print("🚀 AILA Triage - Treinamento de Modelo")
    print("=" * 80)
    
    # 1. Carregar dados
    df = load_data(args.data)
    
    # 2. Treinar modelo
    pipeline = train_model(df)
    
    # 3. Testar com exemplos
    test_model(pipeline)
    
    # 4. Salvar modelo
    save_model(pipeline, args.output)
    
    print("\n✅ Treinamento concluído!")
    print("\n📝 Próximos passos:")
    print(f"   1. Copiar {args.output} para a pasta do projeto")
    print("   2. Atualizar aila_triage.py para usar este modelo")
    print("   3. Testar a API com os novos dados")


if __name__ == "__main__":
    main()
