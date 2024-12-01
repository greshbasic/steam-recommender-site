import json
import random
import re
from django.shortcuts import render
from django.http import HttpResponse
import psycopg2
import requests
from bs4 import BeautifulSoup
from steam_app.db_utils import connect_to_db, check_if_user_exists
from steam_app.recommend import handle_recommendation


POSTGRES_CONFIG = {
    "dbname": "steam_users_db",
    "user": "gresh",
    "password": "dog123",
    "host": "localhost",
    "port": 5432
}

STEAM_API_KEY = "D7174380011DF58873E47B87D86A8CA7"

NEBULA_ID = "76561199521687451"

last_used_steam_id = NEBULA_ID

# Create your views here.
def home(request):
    global last_used_steam_id
    game, game_link, game_cover = None, None, None
    if request.method == 'POST' or 'recommend_another' in request.POST:
        steam_id = request.POST.get('user_input', '')
        if steam_id:
            last_used_steam_id = steam_id
        else:
            steam_id = last_used_steam_id
        connect_to_db()
        user_exists, tags = check_if_user_exists(steam_id)
        game, game_link, game_cover = handle_recommendation(steam_id, user_exists, tags)
        print(game)
        print(game_link)
        print(game_cover)
        
  
    return render(request, 'steam_app/input_form.html', {'game': game, 'link': game_link, 'cover': game_cover})