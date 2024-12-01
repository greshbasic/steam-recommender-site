import psycopg2
import json
from steam_app.config import POSTGRES_CONFIG

def connect_to_db():
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

def check_if_user_exists(steam_id):
    try:
        connection = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE steamid=%s", (steam_id,))
        result = cursor.fetchone()
        if result:
            print(f"User with ID {steam_id} found in DB!")
            if isinstance(result[1], str):
                return (True, json.loads(result[1]))
            else:
                return (True, result[1])
        print(f"User with ID {steam_id} not found in DB.")
        return (False, None)
    except Exception as e:
        print(f"Error: {e}")
        return (False, None)
    finally:
        cursor.close()
        connection.close()

def save_user_to_db(steam_id, tags):
    try:
        connection = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (steamid, weighted_tags)
            VALUES (%s, %s)
            ON CONFLICT (steamid)
            DO UPDATE SET weighted_tags = EXCLUDED.weighted_tags;
        """, (steam_id, tags))
        connection.commit()
        print(f"User with ID {steam_id} saved to database.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()