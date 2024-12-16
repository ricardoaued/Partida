import os
from pathlib import Path

def create_file(path, content=""):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_structure(base_path, structure_dict):
    for name, content in structure_dict.items():
        path = base_path / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content)
        else:
            create_file(path, content)

def main():
    project_root = Path(__file__).parent
    structure = {
        "app": {
            "__init__.py": "",
            "data_fetcher.py": '''# app/data_fetcher.py
from statsbombpy import sb
import json

def get_match_data(match_id: int):
    """
    Busca os dados brutos de uma partida usando o StatsBombPy.
    """
    try:
        match = sb.match(match_id)
        return match
    except Exception as e:
        print(f"Erro ao buscar dados da partida {match_id}: {e}")
        return None
''',
            "api.py": '''# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .summarizer import summarize_match
from .player_profile import get_player_profile
from .narrator import generate_narrative

app = FastAPI(title="Football Match Analysis API")

class MatchSummaryRequest(BaseModel):
    match_id: int

class MatchSummaryResponse(BaseModel):
    summary: str

class PlayerProfileRequest(BaseModel):
    match_id: int
    player_id: int

class PlayerProfileResponse(BaseModel):
    name: str
    passes: int
    finalizations: int
    dispossessions: int
    minutes_played: int

class NarrationRequest(BaseModel):
    match_id: int
    style: Optional[str] = "Formal"

class NarrationResponse(BaseModel):
    narrative: str

@app.post("/match_summary", response_model=MatchSummaryResponse)
def match_summary(request: MatchSummaryRequest):
    summary = summarize_match(request.match_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Partida não encontrada ou erro na sumarização.")
    return {"summary": summary}

@app.post("/player_profile", response_model=PlayerProfileResponse)
def player_profile(request: PlayerProfileRequest):
    profile = get_player_profile(request.match_id, request.player_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Jogador não encontrado na partida.")
    return profile

@app.post("/narrate_match", response_model=NarrationResponse)
def narrate_match(request: NarrationRequest):
    narrative = generate_narrative(request.match_id, request.style)
    if not narrative:
        raise HTTPException(status_code=404, detail="Erro na geração da narrativa.")
    return {"narrative": narrative}
''',
            "summarizer.py": '''# app/summarizer.py
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
''',
            "player_profile.py": '''# app/player_profile.py
# app/player_profile.py
from statsbombpy import sb

def get_player_profile(match_id: int, player_id: int) -> dict:
    match_events = sb.events(match_id)
    type_data = match_events['type']
    player_name_data = match_events['player']
    player_id_data = match_events['player_id']
    minute_data = match_events['minute']

    if player_id in player_id_data:
        return {}
    profile = {
        "name": "",
        "passes": 0,
        "finalizations": 0,
        "dispossessions": 0,
        "minutes_played": 0
    }
    max_minute, min_minute = -1, -1
    for i in range(len(type_data)):
        if player_id != player_id_data[i]:
            continue
        
        event_type = type_data[i]
        if profile["name"] == "":
            profile["name"] = player_name_data[i]
        if event_type == 'Pass':
            profile["passes"] += 1
        elif event_type in ['Shot', 'Goal']:
            profile["finalizations"] += 1
        elif event_type == 'Tackle':
            profile["dispossessions"] += 1
        
        if int(minute_data[i]) > max_minute:
            max_minute = int(minute_data[i])
        if int(minute_data[i]) < min_minute or min_minute == -1:
            min_minute = int(minute_data[i])
    profile["minutes_played"] = max_minute - min_minute + 1

    return profile
''',
            "narrator.py": '''# app/narrator.py
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
'''
        },
        "streamlit_app": {
            "__init__.py": "",
            "main.py": '''# streamlit_app/main.py
import streamlit as st
import requests
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000"

# Initialize session state for inputs and results
if "match_summary" not in st.session_state:
    st.session_state.match_summary = None
if "player_profile" not in st.session_state:
    st.session_state.player_profile = None
if "narration" not in st.session_state:
    st.session_state.narration = None

st.title("Análise de Partidas de Futebol")

# Match ID Input
match_id = st.text_input("Insira o ID da Partida:", value="15946")
if st.button("Buscar Partida"):
    summary_response = requests.post(f"{API_URL}/match_summary", json={"match_id": int(match_id)})
    if summary_response.status_code == 200:
        st.session_state.match_summary = summary_response.json()["summary"]
    else:
        st.error("Erro ao obter a sumarização da partida.")

# Display Match Summary if available
if st.session_state.match_summary:
    st.subheader("Sumarização da Partida")
    st.write(st.session_state.match_summary)

# Player Profile Input
player_id = st.text_input("Insira o ID do Jogador para ver o perfil:", value="5213")
if st.button("Buscar Perfil do Jogador"):
    profile_response = requests.post(f"{API_URL}/player_profile", json={"match_id": int(match_id), "player_id": int(player_id)})
    if profile_response.status_code == 200:
        st.session_state.player_profile = profile_response.json()
    else:
        st.error("Erro ao obter o perfil do jogador.")

# Display Player Profile if available
if st.session_state.player_profile:
    profile = st.session_state.player_profile
    st.subheader("Perfil do Jogador")
    st.json(profile)
    stats = {
        "Passes": profile["passes"],
        "Finalizações": profile["finalizations"],
        "Dispossessions": profile["dispossessions"],
        "Minutos Jogados": profile["minutes_played"]
    }
    fig, ax = plt.subplots()
    ax.bar(stats.keys(), stats.values(), color='skyblue')
    ax.set_ylabel('Quantidade')
    ax.set_title(f'Estatísticas de {profile["name"]}')
    st.pyplot(fig)

# Match Narration Input
style = st.selectbox("Escolha o estilo da narração:", ["Formal", "Humorístico", "Técnico"])
if st.button("Gerar Narração"):
    narration_response = requests.post(f"{API_URL}/narrate_match", json={"match_id": int(match_id), "style": style})
    if narration_response.status_code == 200:
        st.session_state.narration = narration_response.json()["narrative"]
    else:
        st.error("Erro ao gerar a narrativa da partida.")

# Display Match Narration if available
if st.session_state.narration:
    st.subheader("Narração da Partida")
    st.write(st.session_state.narration)
'''
        },
        "docs": {},
        "tests": {},
        "requirements.txt": '''statsbombpy
fastapi
uvicorn
streamlit
langchain
openai
pydantic
requests
matplotlib
python-dotenv
''',
        "README.md": '''# Football Match Analysis Application

## Descrição
Aplicação para análise de partidas de futebol, permitindo gerar perfis de jogadores, sumarizar eventos e criar narrativas personalizadas.

## Configuração do Ambiente
1. Crie e ative o ambiente virtual
2. Instale as dependências: `pip install -r requirements.txt`
3. Crie um arquivo `.env` com sua chave OpenAI: `OPENAI_API_KEY=YOUR_KEY`

## Execução
- API: `uvicorn app.api:app --reload`
- Interface: `streamlit run streamlit_app/main.py`
''',
        ".gitignore": '''# Python
*.pyc
__pycache__/
*.pyo
*.pyd
venv/
ENV/
env/
.env

# VS Code
.vscode/

# PyCharm
.idea/

# Jupyter Notebook
.ipynb_checkpoints/

# macOS
.DS_Store

# Logs
*.log

# Outros
*.sqlite3
match_data.json
'''
    }

    create_structure(project_root, structure)
    print("Estrutura de pastas e arquivos criada com sucesso!")

if __name__ == "__main__":
    main()
