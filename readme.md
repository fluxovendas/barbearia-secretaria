Esse é o projeto de página modelo com chatbo SecretarIA que vamos seguir os seguintes passos:

Passo a Passo Completo com GPT e Dialogflow

Etapa 1: Subir o Projeto para o GitHub

1. Criar um Repositório no GitHub
Acesse GitHub e crie um novo repositório.
Nomeie o repositório como, por exemplo: barbearia-secretaria.
Inicialize o repositório com um README.md.

2. Clonar o Repositório Localmente
No terminal, clone o repositório recém-criado no seu computador:
bash
Copiar código
git clone https://github.com/seu-usuario/barbearia-secretaria.git
cd barbearia-secretaria

3. Organizar a Estrutura de Pastas
Organize sua estrutura de arquivos dentro do repositório da seguinte forma, mantendo sua organização existente:

bash
Copiar código
barbearia-secretaria/
├── docs/                 # Conteúdo para o GitHub Pages (HTML, CSS, JS)
├── bot_backend/           # Código do backend com Flask e integrações
├── README.md              # Documentação do projeto
└── .gitignore             # Para ignorar arquivos desnecessários (ex: credenciais)

4. Adicionar Arquivos e Fazer o Primeiro Commit

Copie seus arquivos atuais para o repositório, como HTML, CSS, JS, e backend.
Faça o primeiro commit:
bash
Copiar código
git add .
git commit -m "Projeto inicial com HTML, CSS, JS e estrutura de backend"
git push origin main

Etapa 2: Colocar a Página Online com GitHub Pages

1. Configurar GitHub Pages
No repositório no GitHub, vá até Settings > Pages.
Em Source, selecione a branch main e o diretório docs/.
O GitHub Pages vai gerar uma URL para o seu site, por exemplo: https://seu-usuario.github.io/barbearia-secretaria.

2. Verificar se a Página Está Online
Acesse a URL gerada e verifique se sua página HTML está disponível e funcional.

3. Commit para Manter as Atualizações
Sempre que fizer mudanças no HTML, CSS ou JS da página, faça o commit e o push:
bash
Copiar código
git add .
git commit -m "Atualizando o layout ou funcionalidades"
git push origin main

Etapa 3: Configuração do Backend com GPT, WhatsApp e Google Calendar

1. Configurar o Backend com Flask, GPT, WhatsApp e Google Calendar
Crie a Pasta bot_backend/

Dentro do repositório, crie a pasta bot_backend/ para armazenar o código do webhook e as integrações.
Crie o Arquivo webhook.py

No diretório bot_backend/, crie o arquivo webhook.py com o seguinte conteúdo, agora incluindo a integração com o Google Calendar:
python

Copiar código

from flask import Flask, request, jsonify
import openai
from twilio.rest import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuração da API OpenAI e Twilio
openai.api_key = 'SUA_CHAVE_OPENAI'
account_sid = 'SEU_ACCOUNT_SID'
auth_token = 'SEU_AUTH_TOKEN'
twilio_client = Client(account_sid, auth_token)

TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Número do WhatsApp sandbox

# Configuração da API Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    user_query = req['queryResult']['queryText']  # Captura a pergunta do usuário
    user_phone = req['originalDetectIntentRequest']['payload']['data']['from']  # Número do usuário

    # GPT: Gerar resposta
    gpt_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=user_query,
        max_tokens=150
    )
    response_text = gpt_response['choices'][0]['text'].strip()

    # Verificar se a intenção é verificar horários disponíveis
    if "horários" in user_query.lower():
        available_slots = check_availability()
        response_text = f"Horários disponíveis: {', '.join(available_slots)}"
    
    # Twilio: Enviar resposta pelo WhatsApp
    message = twilio_client.messages.create(
        body=response_text,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{user_phone}'
    )

    return jsonify({"fulfillmentText": response_text})

def check_availability():
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    available_slots = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        available_slots.append(start)
    return available_slots

def schedule_notifications(event_id, client_phone, barber_phone):
    # Schedule notifications at 1 hour, 10 minutes, and on time
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    start_time = datetime.fromisoformat(event['start']['dateTime'])

    notification_times = [
        (start_time - timedelta(hours=1), "Falta 1 hora para o seu compromisso."),
        (start_time - timedelta(minutes=10), "Faltam 10 minutos para o seu compromisso."),
        (start_time, "É hora do seu compromisso!")
    ]

    for notify_time, message_text in notification_times:
        # Lógica para agendar envio de mensagens pelo Twilio no horário correto (usar Celery, cron job, etc.)
        # Aqui vamos apenas simular o envio imediato
        twilio_client.messages.create(
            body=message_text,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{client_phone}'
        )
        twilio_client.messages.create(
            body=message_text,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{barber_phone}'
        )

if __name__ == '__main__':
    app.run(port=5000, debug=True)

Criar o Arquivo requirements.txt

Dentro da pasta bot_backend/, crie o arquivo requirements.txt com as dependências:
txt
Copiar código
Flask
openai
twilio
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
Credenciais do Google Calendar

Coloque o arquivo credentials.json que contém as credenciais do Google Calendar dentro da pasta bot_backend/.
Rodar o Backend Localmente

No terminal, navegue até bot_backend/ e execute o seguinte comando para instalar as dependências e rodar o servidor Flask:
bash
Copiar código
pip install -r requirements.txt
python webhook.py
2. Subir o Backend para o GitHub
Commit para Subir o Backend
Após configurar o backend, faça um commit e push:
bash
Copiar código
git add bot_backend/
git commit -m "Configuração do backend com Flask, GPT, WhatsApp e Google Calendar"
git push origin main
Etapa 4: Configuração do Dialogflow
1. Criar o Agente no Dialogflow
Acessar o Dialogflow

Crie um novo agente no Dialogflow, configure o idioma como Português (Brasil) e nomeie-o como SecretarIA.
Criar Intenção Genérica

Intenção Genérica "Consultas"

No Dialogflow, crie uma intenção genérica chamada "Consultas".
Adicione frases de exemplo como:
"Quanto custa um corte de cabelo?"
"Quais são os horários disponíveis?"
"Que serviços vocês oferecem?"
Habilitar o Webhook

Marque a opção Enable webhook call for this intent na intenção "Consultas". Assim, qualquer pergunta feita será enviada para o webhook, onde o GPT gerará a resposta ou verificará a disponibilidade no Google Calendar.
2. Configurar o Webhook no Dialogflow
Acessar a Aba de Fulfillment

No painel do Dialogflow, vá até a aba Fulfillment e cole o URL do webhook gerado pelo ngrok (ou outro serviço).
Usar ngrok para Expor o Servidor Local

No terminal, rode o comando ngrok para expor o webhook:
bash
Copiar código
ngrok http 5000
Copie o URL gerado pelo ngrok (ex: https://abcd1234.ngrok.io/webhook) e cole-o no Dialogflow.
Testar o Bot

Use o simulador no Dialogflow para testar as intenções que você criou. Pergunte, por exemplo, "Quais são os horários?" e veja se o bot responde corretamente, verificando a disponibilidade no Google Calendar.
3. Commit para Subir as Configurações do Dialogflow
Sempre que configurar novas intenções ou modificar o webhook, faça um commit:
bash
Copiar código
git add .
git commit -m "Configuração do webhook e intenções no Dialogflow com Google Calendar"
git push origin main
Etapa 5: Notificações pelo Google Calendar
Notificações Automáticas

Quando um evento for agendado no Google Calendar, o bot pode programar notificações para o cliente e o barbeiro usando Twilio. Isso pode ser feito usando uma tarefa assíncrona com Celery ou cron jobs.
Simulação de Notificações

No código, incluímos uma simulação de envio imediato, mas você pode ajustar a lógica para enviar as mensagens no momento correto usando tarefas programadas.
Etapa 6: Testes e Ajustes Finais
Testar a Integração Completa

Teste o fluxo completo: do agendamento, verificação de horários, até o envio das notificações.
Ajustes e Manutenção

Faça commits frequentes para manter o histórico de mudanças e facilitar a manutenção do código.