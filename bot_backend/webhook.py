from flask import Flask, request, jsonify
import openai
from twilio.rest import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
import os
import time
from docx import Document

app = Flask(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração da API OpenAI e Twilio
openai.api_key = os.getenv('OPENAI_API_KEY')
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(account_sid, auth_token)

TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')  # Número do WhatsApp sandbox

# Configuração da API Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Caminho do arquivo Word com as informações da barbearia
word_file_path = 'gpt.docx'  # Nome do arquivo atualizado para gpt.docx

# Função para ler o conteúdo do arquivo Word
def read_word_file(filepath):
    doc = Document(filepath)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Leitura do conteúdo do arquivo Word
context = read_word_file(word_file_path)

# Dicionário para manter o estado do atendimento por número de telefone
active_sessions = {}
session_timeout = 15 * 60  # 15 minutos de inatividade

# Função para criar eventos recorrentes
def create_recurring_events():
    calendar_id = 'primary'
    barbeiro = "Barbeiro X"

    start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    for day in range(0, 6):  # 0 = Monday, 5 = Saturday
        for hour in range(8, 18):
            start_time = start_time.replace(hour=hour, minute=0)
            end_time = start_time + timedelta(hours=1)

            event = {
                'summary': f'{barbeiro} - Disponível',
                'location': 'Barbearia X',
                'description': 'Horário disponível para agendamento.',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'recurrence': [
                    'RRULE:FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR,SA'
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }

            service.events().insert(calendarId=calendar_id, body=event).execute()

# Função para buscar horários disponíveis no Google Calendar
def check_availability():
    calendar_id = 'primary'
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    available_slots = []

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        available_slots.append(start)

    return available_slots

# Webhook principal
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    user_query = req['queryResult']['queryText'].lower()
    user_phone = req['originalDetectIntentRequest']['payload']['data']['from']

    # Palavra-chave para ativar o processamento
    keyword = "teste secretaria"

    current_time = time.time()

    if keyword in user_query or (user_phone in active_sessions and current_time - active_sessions[user_phone] < session_timeout):
        active_sessions[user_phone] = current_time

        if keyword in user_query:
            # Responder com a mensagem de introdução impressionante
            response_text = (
                "Olá! Sou a SecretarIA, sua assistente virtual, mas tão humanizada que você nem vai perceber que está falando com um robô. 😊 "
                "Vamos começar a demonstração do seu atendimento? Aqui, você pode realizar agendamentos que serão automaticamente integrados com nosso sistema de calendário, "
                "descobrir nossos serviços e preços, e obter qualquer outra informação sobre a barbearia. Como posso ajudar você hoje?"
            )
        elif "horários" in user_query:
            available_slots = check_availability()
            slots_text = ', '.join(available_slots)
            response_text = f"Os horários disponíveis são: {slots_text}. Como posso ajudá-lo com isso?"
        else:
            prompt = f"{context}\n\nPergunta: {user_query}\nResposta:"
            gpt_response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=150
            )
            response_text = gpt_response['choices'][0]['text'].strip()

        # Twilio: Enviar resposta pelo WhatsApp
        message = twilio_client.messages.create(
            body=response_text,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{user_phone}'
        )

        return jsonify({"fulfillmentText": response_text})

    # Se a palavra-chave não estiver presente, não faz nada e não envia nenhuma resposta
    return '', 200  # HTTP 200 OK, sem conteúdo

if __name__ == '__main__':
    app.run(port=5000, debug=True)