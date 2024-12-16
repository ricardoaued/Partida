# app/summarizer.py

from openai import OpenAI
from dotenv import load_dotenv
import os
from statsbombpy import sb
from typing import List

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a chave da API da OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_key_events(match_id: int) -> List[dict]:
    """
    Retorna uma lista de eventos-chave (gols, cartões, substituições, chutes) da partida.
    """
    match_events = sb.events(match_id)
    type_data = match_events['type']
    team_data = match_events['team']
    player_data = match_events['player']
    minute_data = match_events['minute']

    key_events = []
    for i in range(len(type_data)):
        if type_data[i] in ['Goal', 'Card', 'Substitution', 'Shot']:
            key_events.append({
                'type': type_data[i],
                'team': team_data[i],
                'player': player_data[i],
                'minute': int(minute_data[i])
            })
        # event_type = event['type']['name']
        # if event_type in ['Goal', 'Card', 'Substitution', 'Shot']:
        #     key_events.append(event)
    return key_events

def summarize_match(match_id: int) -> str:
    """
    Gera um resumo textual dos principais eventos da partida usando a API da OpenAI.
    """
    key_events = get_key_events(match_id)
    if not key_events:
        return "Nenhum evento principal encontrado para esta partida."

    # Cria um prompt detalhado para a API
    summary_prompt = "Resuma os seguintes eventos de uma partida de futebol:\n\n"
    for event in key_events:
        minute = event.get('minute', 'N/A')
        event_type = event['type']
        player = event['player'] if event.get('player') else 'N/A'
        team = event['team'] if event.get('team') else 'N/A'
        summary_prompt += f"{minute}': {event_type} por {player} do time {team}\n"

    summary_prompt += "\nResumo:"

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": summary_prompt,
                }
            ],
            model="gpt-4o"
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Erro na sumarização: {e}")
        return "Não foi possível gerar a sumarização da partida."
