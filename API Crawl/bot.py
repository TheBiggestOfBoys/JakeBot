import os
import random
import requests
import time
from dotenv import load_dotenv
import pyttsx3

# Load environment variables from .env file
load_dotenv()

bot_id = os.getenv('BOT_ID')
group_id = os.getenv('GROUP_ID')
access_token = os.getenv('ACCESS_TOKEN')

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

def get_latest_message():
    url = f'https://api.groupme.com/v3/groups/{group_id}/messages'
    params = {
        'token': access_token,
        'limit': 1  # Only retrieve the latest message
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving messages: {e}")
        return None

def get_path(fileName):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    return os.path.join(parent_dir, 'Data', fileName)

def get_quote(filepath):
    try:
        print(f"Attempting to read file: {filepath}")
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return None
        with open(filepath, 'r', encoding='utf-8') as file:
            quotes = [line.strip() for line in file.readlines()]
            print("Read quotes")
        if quotes:
            return random.choice(quotes)
        else:
            print("No quotes found in file.")
            return None
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

def listen_for_messages():
    print("Listening for messages...")
    last_message_id = None
    last_message_text = None
    while True:
        messages = get_latest_message()
        if messages and 'response' in messages and 'messages' in messages['response']:
            message = messages['response']['messages'][0]
            current_message_text = message['text']
            if last_message_id is None or message['id'] > last_message_id:
                last_message_id = message['id']
                if message['sender_type'] == 'user':
                    if current_message_text != last_message_text:
                        print(f"New message: {current_message_text}")
                        last_message_text = current_message_text
                    if random.random() < 0.5:
                        print("Sending message")
                        quotes_path = get_path('quotes.txt')
                        quote = get_quote(quotes_path)
                        print(f"Retrieved quote: {quote}")
                        if quote:
                            print("Sending quote to group...")
                            send_message(quote)
                            print("Speaking quote")
                            speak_text(quote)
                        else:
                            print("Error: Could not retrieve quote.")
        time.sleep(1)

if __name__ == '__main__':
    listen_for_messages()