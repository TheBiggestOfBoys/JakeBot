import os
import random
import requests
import time
import sys
from dotenv import load_dotenv
import pyttsx3
import logging

# Load environment variables
load_dotenv()

# Constants
BOT_ID = os.getenv('BOT_ID')
GROUP_ID = os.getenv('GROUP_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
GROUPME_MESSAGES_URL = f'https://api.groupme.com/v3/groups/{GROUP_ID}/messages'
GROUPME_POST_URL = 'https://api.groupme.com/v3/bots/post'
REQUEST_PARAMS = {'token': ACCESS_TOKEN, 'limit': 1}
DATA_DIR = 'Data'
RESPONSE_TYPES = ['text', 'media', 'both']
MEDIA_TYPES = ['images', 'gifs', 'videos']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Message sending functions
def send_message(text=None, image_url=None, video_url=None):
    payload = {'bot_id': BOT_ID, 'text': text if text else ""}
    attachments = []
    if image_url:
        attachments.append({'type': 'image', 'url': image_url})
    if video_url:
        attachments.append({'type': 'video', 'url': video_url})
    if attachments:
        payload['attachments'] = attachments
    try:
        response = requests.post(GROUPME_POST_URL, json=payload)
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.content}")
        response.raise_for_status()
        if response.content:
            return response.json()
        else:
            logging.info("Message sent successfully with no response body.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")
        return None

def get_latest_message():
    try:
        response = requests.get(GROUPME_MESSAGES_URL, params=REQUEST_PARAMS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving messages: {e}")
        return None

def listen_for_messages(response_percentage, pause_interval):
    logging.info("Listening for messages...")
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
                        logging.info(f"New message: {current_message_text}")
                        last_message_text = current_message_text
                    if random.random() < response_percentage:
                        logging.info("Sending message")
                        quote = None
                        media_url = None

                        response_type = random.choice(RESPONSE_TYPES)
                        if response_type in ['text', 'both']:
                            quote = get_line(os.path.join(DATA_DIR, 'quotes.txt'))
                            logging.info(f"Retrieved quote: {quote}")

                        if response_type in ['media', 'both']:
                            media_type_choice = random.choice(MEDIA_TYPES)
                            media_links_path = os.path.join(DATA_DIR, f"{media_type_choice}.txt")
                            media_url = get_line(media_links_path)
                            logging.info(f"Retrieved media URL: {media_url}")

                        if quote or media_url:
                            if response_type == 'text':
                                logging.info("Sending text only")
                                send_message(text=quote)
                                speak_text(quote)
                            elif response_type == 'media':
                                logging.info("Sending media only")
                                send_message(image_url=media_url if media_type_choice in ['images', 'gifs'] else None,
                                             video_url=media_url if media_type_choice == 'videos' else None)
                            elif response_type == 'both':
                                logging.info("Sending text and media")
                                send_message(text=quote,
                                             image_url=media_url if media_type_choice in ['images', 'gifs'] else None,
                                             video_url=media_url if media_type_choice == 'videos' else None)
                                speak_text(quote)
        time.sleep(pause_interval)

def get_line(filepath):
    try:
        logging.info(f"Attempting to read file: {filepath}")
        if not os.path.exists(filepath):
            logging.warning(f"File does not exist: {filepath}")
            return None
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
        if lines:
            return random.choice(lines)
        else:
            logging.warning(f"No lines found in file: {filepath}")
            return None
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return None

def speak_text(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        logging.info(f"Spoken text: {text}")
    except Exception as e:
        logging.error(f"Error speaking text: {e}")
        
# Fun Functions
def hardly_know_her(word):
	if (word.__contains__("er")):
		print(word + " her, I hardly know her!")
        
def quotify(string):
    words = string.split()
    temp = ""
    for word in words:
        if (random.random() < 0.35):
            temp += '"' + word + '" '
        else:
            temp += word + ' '
    return temp

if __name__ == '__main__':
    try:
        # Parse command-line arguments
        if len(sys.argv) != 3:
            print("Usage: python bot.py <response_percentage> <pause_interval>")
            sys.exit(1)

        response_percentage = float(sys.argv[1])
        pause_interval = int(sys.argv[2])

        # Validate arguments
        if not (0.0 <= response_percentage <= 1.0):
            print("Error: response_percentage must be between 0.0 and 1.0")
            sys.exit(1)
        if pause_interval <= 0:
            print("Error: pause_interval must be a positive integer")
            sys.exit(1)

        # Start the bot
        listen_for_messages(response_percentage, pause_interval)
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
