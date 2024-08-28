from openai import OpenAI
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o cliente OpenAI com a chave da API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Faz uma chamada para criar uma conclusão de chat
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Escreva um poema sobre a natureza em português."}
    ]
)

# Imprime a resposta da API
print(completion.choices[0].message['content'])