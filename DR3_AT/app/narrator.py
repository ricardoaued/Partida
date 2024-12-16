# app/narrator.py

from openai import OpenAI
from dotenv import load_dotenv
import os
from .summarizer import get_key_events
from typing import List

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a chave da API
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_narrative(match_id: int, style: str = "Formal") -> str:
    key_events = get_key_events(match_id)
    if not key_events:
        return "Nenhum evento encontrado para gerar a narrativa."

    events_desc = ""
    for event in key_events:
        minute = event.get('minute', 'N/A')
        event_type = event['type']
        player = event['player'] if event.get('player') else 'N/A'
        team = event['team'] if event.get('team') else 'N/A'
        # Linha corrigida: adicionamos \n ao final da string e não deixamos a string aberta em múltiplas linhas
        events_desc += f"Aos {minute}' minuto, {player} do {team} realizou um(a) {event_type.lower()}.\n"

    prompt = f"Crie uma narrativa {style.lower()} para a partida de futebol com os seguintes eventos:\n\n{events_desc}\nNarrativa:"

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o"
        )
        narrative = response.choices[0].message.content.strip()
        return narrative
    except Exception as e:
        print(f"Erro na geração de narrativa: {e}")
        return "Não foi possível gerar a narrativa da partida."
