import os
import random
import requests
import time
import sys
from dotenv import load_dotenv
import pyttsx3
import logging

#region Constants
load_dotenv()
BOT_ID = os.getenv('BOT_ID')
GROUP_ID = os.getenv('GROUP_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
GROUPME_MESSAGES_URL = f'https://api.groupme.com/v3/groups/{GROUP_ID}/messages'
GROUPME_POST_URL = 'https://api.groupme.com/v3/bots/post'
REQUEST_PARAMS = {'token': ACCESS_TOKEN, 'limit': 1}
DATA_DIR = 'Data'
RESPONSE_TYPES = ['text', 'media', 'both']
MEDIA_TYPES = ['images', 'gifs', 'videos']
logging.basicConfig(level=logging.INFO)

# Name to User ID mapping
NAME_TO_USER_ID = {
    "Noah Davelaar": "57383311",
    "Zeke Roher": "94102137",
    "Carter Steele": "122250018",
    "Kyle Dagman": "124700938",
    "Caleb Schwartz": "106705486",
    "Marcus Bradley": "110543789",
    "Gavin Harris": "99314407",
    "Will Norris": "106903726",
    "Peter Andrulis": "124821503",
    "Joey Heaston": "74159751",
    "Levin Smith": "125014222",
    "Caleb Black": "92588534",
    "Solomon Campbell": "88670721",
    "Seth Reed": "115839177",
    "Carter Newman": "121600369",
    "Sam Hryszczuk": "124899656",
    "Eli King": "87748624",
    "Benjamin Magana": "89586028",
    "Nate Taylor": "125034801",
    "Brennan Miller": "124263586",
    "Dylan VanderGoot": "121758820",
    "Kyle Thomas": "114408323",
    "Sergio Membreno": "112464651",
    "David Zgarta": "96448587",
    "Daniel Bishop": "116366778",
    "Isaac Terrell": "116455020",
    "Noah Lien": "119550369",
    "Jared Shafer": "50056945",
    "Keegan Matheson": "50494264",
    "Samuel Maurer": "82242542",
    "Tavin Reeves": "57580921",
    "Erik Allen": "54236065",
    "Caleb Bell": "96325934",
    "John Kuligowski": "95688396",
    "Matt Snyder": "105606685",
    "Micah Smith": "105606686",
    "Mark Lee": "88853984",
    "Elijah Ladd": "101124613",
    "Garrett Vandermark": "105606687",
    "Logan Trier": "105599421",
    "Coby Peters": "88960626",
    "Owen Slayton": "94391709",
    "Garrett Vandermark": "80207822",
    "Kyle Hirschelman": "105616963",
    "Joshua Blume": "105623144",
    "Tommy Walatka": "62180191",
    "Darin Jordan": "72134982",
    "Dayton Molendorp": "91815787",
    "Wyatt Atzhorn": "112826040",
    "Josh Benson": "87824796",
    "Case Anderson": "75172758",
    "Max Burger": "104007656",
    "Gabriel Osborn": "55685227",
    "Ethan Occhipinti": "116348050",
    "Mitchell Melfe": "101458043",
    "Nick Cavey": "73636638",
    "David Castro": "116407125",
    "Jake Scott": "74617923",
    "Martin Didier": "61090418",
    "Elijah Pennington": "88265724",
    "Miguel Salcedo": "105332694"
}

USER_ID_TO_NAME = {uid: name for name, uid in NAME_TO_USER_ID.items()}
#endregion

#region Message Sending Functions
def send_message(text=None, image_url=None, video_url=None, user_id=None, reply_id=None):
    """
    Send a message with optional text, image, video, mention, and reply.
    At least one of text, image_url, or video_url must be provided.
    For video, attaches a preview_url (video_url with .jpg extension).
    """
    if not any([text, image_url, video_url]):
        logging.warning("send_message called with no content. Aborting send.")
        return None

    payload = {'bot_id': BOT_ID, 'text': text or ""}
    attachments = []

    if image_url:
        attachments.append({'type': 'image', 'url': image_url})
    if video_url:
        if video_url.endswith('.mp4'):
            # Replace domain and extension for preview_url
            preview_url = video_url[:-3] + 'jpg'
            attachments.append({'type': 'video', 'url': video_url, 'preview_url': preview_url})
        else:
            logging.warning("Video URL does not end with .mp4, skipping video.")
    if user_id:
        user_name = USER_ID_TO_NAME.get(user_id, "user")
        mention_text = f"@{user_name}"
        # Always start the message with the mention
        if payload['text']:
            payload['text'] = f"{mention_text} {payload['text']}"
        else:
            payload['text'] = mention_text
        # loci: [[start_index, length of mention]]
        attachments.append({
            "type": "mentions",
            "user_ids": [user_id],
            "loci": [[0, len(mention_text)]]
        })
    if reply_id:
        attachments.append({
            "type": "reply",
            "reply_id": reply_id,
            "base_reply_id": reply_id
        })
    if attachments:
        payload['attachments'] = attachments

    try:
        response = requests.post(GROUPME_POST_URL, json=payload)
        logging.info(f"Status: {response.status_code}, Content: {response.content}")
        response.raise_for_status()
        return response.json() if response.content else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")
        return None
#endregion

#region Utility Functions
def get_random_line(filepath):
    try:
        if not os.path.exists(filepath):
            logging.warning(f"File does not exist: {filepath}")
            return None
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        return random.choice(lines) if lines else None
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return None

def speak_text(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Error speaking text: {e}")
        
def get_latest_message():
    try:
        response = requests.get(GROUPME_MESSAGES_URL, params=REQUEST_PARAMS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving messages: {e}")
        return None
#endregion

#region Main Bot Logic
def like_message(message_id):
    """
    Likes a message in the group using the bot's access token.
    """
    url = f"https://api.groupme.com/v3/messages/{GROUP_ID}/{message_id}/like"
    params = {"token": ACCESS_TOKEN}
    try:
        response = requests.post(url, params=params)
        logging.info(f"Liked message {message_id}: {response.status_code}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error liking message: {e}")
        return False

def listen_for_messages(response_percentage, pause_interval, like_percentage=0.7):
    last_message_id = None
    last_message_text = None
    last_user_id = None  # Store the last user_id for mentioning
    while True:
        last_message = get_latest_message()
        if last_message and 'response' in last_message and 'messages' in last_message['response']:
            message = last_message['response']['messages'][0]
            if last_message_id is None or message['id'] > last_message_id:
                last_message_id = message['id']
                if message['sender_type'] == 'user':
                    current_message_text = message['text']
                    current_user_id = message.get('user_id')
                    if current_message_text != last_message_text:
                        last_message_text = current_message_text
                        last_user_id = current_user_id

                        # Randomly like the message with a higher probability
                        if random.random() < like_percentage:
                            like_message(last_message_id)

                        # Randomly decide to respond
                        if random.random() < response_percentage:
                            include_text = random.choice([True, False])
                            include_media = random.choice([True, False])
                            include_mention = random.choice([True, False])

                            # Ensure at least one content type is included
                            if not include_text and not include_media:
                                if random.choice([True, False]):
                                    include_text = True
                                else:
                                    include_media = True

                            text = None
                            image_url = None
                            video_url = None

                            if include_text:
                                text = get_random_line(os.path.join(DATA_DIR, 'quotes.txt'))

                            if include_media:
                                media_type = random.choice(MEDIA_TYPES)
                                media_url = get_random_line(os.path.join(DATA_DIR, f"{media_type}.txt"))
                                if media_type in ['images', 'gifs']:
                                    image_url = media_url
                                else:
                                    video_url = media_url

                            mention_user_id = last_user_id if include_mention else None

                            if text or image_url or video_url:
                                send_message(
                                    text=text,
                                    image_url=image_url,
                                    video_url=video_url,
                                    user_id=mention_user_id,
                                    reply_id=last_message_id
                                )
                                if text:
                                    speak_text(text)
        time.sleep(pause_interval)
#endregion

#region Entry Point
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python bot.py <response_percentage> <pause_interval> [like_percentage]")
        sys.exit(1)
    response_percentage = float(sys.argv[1])
    pause_interval = int(sys.argv[2])
    like_percentage = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
    listen_for_messages(response_percentage, pause_interval, like_percentage)
#endregion
