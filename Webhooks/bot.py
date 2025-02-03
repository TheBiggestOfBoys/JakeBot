import os
import random
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pyttsx3
import threading
import subprocess
import platform

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

bot_id = os.getenv('BOT_ID')
ngrok_path = os.getenv('NGROK_PATH')

def send_message(text):
    url = 'https://api.groupme.com/v3/bots/post'
    payload = {
        'bot_id': bot_id,
        'text': text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Message sent: {text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return None

def get_quote(filepath):
    try:
        with open(filepath, 'r') as file:
            quotes = file.readlines()
        return random.choice(quotes).strip()
    except Exception as e:
        print(f"Error reading quotes file: {e}")
        return None

def speak_text(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        print(f"Spoken text: {text}")
    except Exception as e:
        print(f"Error speaking text: {e}")

def get_path(fileName):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    return os.path.join(parent_dir, 'Data', fileName)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data['sender_type'] == 'user':
        if random.random() < 0.1:
            quotes_path = get_path('quotes.txt')

            quote = get_quote(quotes_path)
            if quote:
                send_message(quote)
                speak_text(quote)
            else:
                print("Error: Could not retrieve quote.")
    return jsonify(status="success"), 200

def run_flask():
    app.run(port=5000)

def run_ngrok():
    if platform.system() == "Windows":
        subprocess.Popen(['start', 'cmd', '/k', f'{ngrok_path + '/groupme'} http 5000'], shell=True)
    else:
        subprocess.Popen(['gnome-terminal', '--', f'{ngrok_path + '/groupme'} http 5000'])

if __name__ == '__main__':
    # Start ngrok first
    ngrok_thread = threading.Thread(target=run_ngrok)
    ngrok_thread.start()

    # Wait for a few seconds to ensure ngrok is up and running
    import time
    time.sleep(5)

    # Start Flask application
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Join threads
    ngrok_thread.join()
    flask_thread.join()
