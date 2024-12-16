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
