from flask import Flask, request, jsonify
import openai
from twilio.rest import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser  # Biblioteca para parsing de datas e horários
from dotenv import load_dotenv
import os

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


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    # Captura a pergunta do usuário
    user_query = req['queryResult']['queryText']
    # Número do usuário
    user_phone = req['originalDetectIntentRequest']['payload']['data']['from']

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

    # Verificar se a intenção é agendar
    elif "agendar" in user_query.lower():
        # Extrai o horário escolhido pelo cliente
        selected_time = extract_time_from_query(user_query)
        event_id = schedule_appointment(selected_time)
        # Substitua pelo número do barbeiro
        send_confirmation(user_phone, "whatsapp:+5561998765432", selected_time)
        response_text = "Seu agendamento foi confirmado!"

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


def schedule_appointment(start_time, summary="Appointment", description="Agendamento via WhatsApp"):
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('id')


def send_confirmation(client_phone, barber_phone, event_time):
    confirmation_message = f"Seu agendamento foi confirmado para {event_time}. Nos vemos em breve!"
    twilio_client.messages.create(
        body=confirmation_message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{client_phone}'
    )
    twilio_client.messages.create(
        body=f"Novo agendamento marcado para {event_time}.",
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{barber_phone}'
    )


def extract_time_from_query(query):
    # Exemplo simples de extração de horário usando parsing de linguagem natural
    try:
        date_time_obj = parser.parse(query, fuzzy=True)
        return date_time_obj.isoformat()
    except ValueError:
        return None  # Retorne None ou uma string padrão se não conseguir identificar a data/hora


if __name__ == '__main__':
    app.run(port=5000, debug=True)