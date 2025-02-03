import os
import random
import requests
import time
from dotenv import load_dotenv
import pyttsx3

load_dotenv()

bot_id = os.getenv('BOT_ID')
group_id = os.getenv('GROUP_ID')
access_token = os.getenv('ACCESS_TOKEN')

def send_message(text=None, image_url=None, video_url=None):
    url = 'https://api.groupme.com/v3/bots/post'
    payload = {
        'bot_id': bot_id,
        'text': text if text else ""
    }
    attachments = []
    if image_url:
        attachments.append({
            'type': 'image',
            'url': image_url
        })
    if video_url:
        attachments.append({
            'type': 'video',
            'url': video_url
        })
    if attachments:
        payload['attachments'] = attachments
    try:
        response = requests.post(url, json=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        response.raise_for_status()
        if text and (image_url or video_url):
            print("Message sent: Text and Media")
        elif text:
            print("Message sent: Text only")
        elif image_url or video_url:
            print("Message sent: Media only")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return None

def get_latest_message():
    url = f'https://api.groupme.com/v3/groups/{group_id}/messages'
    params = {
        'token': access_token,
        'limit': 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving messages: {e}")
        return None

def get_line(filepath):
    try:
        print(f"Attempting to read file: {filepath}")
        if not os.path.exists(filepath):
            print(f"File does not exist: {filepath}")
            return None
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            print("Read lines")
        if lines:
            return random.choice(lines)
        else:
            print("No lines found in file.")
            return None
    except Exception as e:
        print(f"Error reading file: {e}")
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
                        quote = None
                        media_url = None

                        response_type = random.choice(['text', 'media', 'both'])
                        if response_type in ['text', 'both']:
                            quote = get_line('Data/quotes.txt')
                            print(f"Retrieved quote: {quote}")

                        if response_type in ['media', 'both']:
                            media_type_choice = random.choice(['images', 'gifs', 'videos'])
                            if media_type_choice == 'images':
                                media_links_path = 'Data/images.txt'
                            elif media_type_choice == 'gifs':
                                media_links_path = 'Data/gifs.txt'
                            elif media_type_choice == 'videos':
                                media_links_path = 'Data/videos.txt'
                            media_url = get_line(media_links_path)
                            print(f"Retrieved media URL: {media_url}")

                        if quote or media_url:
                            if response_type == 'text':
                                print("Sending text only")
                                send_message(text=quote)
                                speak_text(quote)
                            elif response_type == 'media':
                                print("Sending media only")
                                send_message(image_url=media_url if media_type_choice in ['images', 'gifs'] else None,
                                             video_url=media_url if media_type_choice == 'videos' else None)
                            elif response_type == 'both':
                                print("Sending text and media")
                                send_message(text=quote,
                                             image_url=media_url if media_type_choice in ['images', 'gifs'] else None,
                                             video_url=media_url if media_type_choice == 'videos' else None)
                                speak_text(quote)
                                
                        print()
        time.sleep(1)

if __name__ == '__main__':
    listen_for_messages()
