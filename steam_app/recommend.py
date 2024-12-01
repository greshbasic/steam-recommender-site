import json
import random
import re
import requests
from bs4 import BeautifulSoup
from steam_app.db_utils import save_user_to_db
from steam_app.config import STEAM_API_KEY

def recommend_games_from_tags(tags):
    if not tags:
        return
    tags = dict(sorted(tags.items(), key=lambda item: item[1], reverse=True))
    top_ten_tags = list(tags.keys())[:10]
    three_random_tags = random.sample(top_ten_tags, 3)
    formatted_tags = [tag.replace(" ", "+") for tag in three_random_tags]
    search_term = "%2C+".join(formatted_tags)
    search_url = f"https://store.steampowered.com/search/?term={search_term}"
    
    all_titles = []
    response = requests.get(search_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        titles = soup.find_all('span', class_='title')
        for title in titles:
            all_titles.append(title.text)

        random_game = random.choice(all_titles)
        return display_recommendations(random_game)
    else:
        print("Unable to access search page.")
        
def display_recommendations(game_name):
    URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        app_list = data["applist"]["apps"]
        appid = None
        for app in app_list:
            if app["name"] == game_name:
                appid = app["appid"]
                break
        if appid:
            game_url = f"https://store.steampowered.com/app/{appid}/{format_game_name_for_url(game_name)}/"
            return (game_name, game_url)
        else:
            return (game_name, None)
    else:
        return (game_name, None)
        
def determine_tags_for_user(steam_id):
    games = get_games_from_user(int(steam_id))
    if not games:
        return
    top_ten_played_games = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)[:10]
    weights = get_weights_for_games(top_ten_played_games)
    weighted_tags_dict = {}
    for game in top_ten_played_games:
        tags = get_tags_from_game(game)
        game_weight = weights[game["appid"]]
        for tag in tags:
            if tag in weighted_tags_dict:
                weighted_tags_dict[tag] += game_weight
            else:
                weighted_tags_dict[tag] = game_weight
        
    sorted_dict = dict(sorted(weighted_tags_dict.items(), key=lambda item: item[1], reverse=True))
    sorted_dict_json = json.dumps(sorted_dict)
    save_user_to_db(steam_id, sorted_dict_json)
    return recommend_games_from_tags(sorted_dict)
    
def get_games_from_user(steam_id):
    URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id,
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json"
    }
    
    try:
        response = requests.get(URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "response" in data and "games" in data["response"]:
            return data["response"]["games"]
        else:
            print("Unable to find games for user, they may have a private profile.")
            return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return []
    
def get_weights_for_games(games):
    sorted_games = sorted(games, key=lambda game: game['playtime_forever'], reverse=True)
    weight_dict = {}
    total_games = len(sorted_games)
    
    for i, game in enumerate(sorted_games):
        appid = game["appid"]
        weight = (total_games - i) / total_games
        weight_dict[appid] = weight
    
    return weight_dict
    
     
def format_game_name_for_url(game_name):
    replaced_string = game_name.replace(" ", "_").replace(":", "").replace("-", "_").replace("'", "")
    title_case_string = replaced_string.title()
    return title_case_string

def get_tags_from_game(game):
    appid = game["appid"]
    game_name = format_game_name_for_url(game["name"])
    URL = f"https://store.steampowered.com/app/{appid}/{game_name}/"
    
    response = requests.get(URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find('script', text=re.compile('InitAppTagModal'))
        script_content = script_tag.string if script_tag else ''
        json_data_match = re.search(r'InitAppTagModal\(\s*\d+,\s*(\[\{.*?\}\])\s*,', script_content)
        if json_data_match:
            json_data = json.loads(json_data_match.group(1))
            tag_names = [tag['name'] for tag in json_data]
            return tag_names
        else:
            print("Unable to find tag data.")
            return []
    else:
        print("Unable to access app page.")
        return []

def handle_recommendation(steam_id, user_exists, tags):
    if user_exists:
        return recommend_games_from_tags(tags)
    else:
        return determine_tags_for_user(steam_id)