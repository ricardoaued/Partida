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
