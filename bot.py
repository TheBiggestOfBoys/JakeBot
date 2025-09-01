"""
GroupMe Bot Server (Python)
---------------------------
Responds to GroupMe messages with random quotes, media, or user callouts.

Features:
- Polls for latest messages (no webhooks needed).
- Randomly replies to messages with configurable probability.
- "Hardly know her" jokes for words ending in 'er'.
- Quotify feature that puts random quotes around words.
- User callouts and mentions.
- Can reply to specific messages.

Environment Variables:
- BOT_ID: The GroupMe Bot ID (required).
- GROUP_ID: The GroupMe Group ID (required for user tagging).
- ACCESS_TOKEN: Your GroupMe user access token (required for user tagging).
"""

import os
import random
import requests
import time
import sys
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# region Constants
load_dotenv()
BOT_ID = os.getenv('BOT_ID')
GROUP_ID = os.getenv('GROUP_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
GROUPME_POST_URL = 'https://api.groupme.com/v3/bots/post'
GROUPME_MESSAGES_URL = f'https://api.groupme.com/v3/groups/{GROUP_ID}/messages'
REQUEST_PARAMS = {'token': ACCESS_TOKEN, 'limit': 1}
DATA_DIR = 'Data'
MEDIA_TYPES = ['images', 'gifs', 'videos']

# Probability settings
RESPONSE_PROBABILITY = float(os.getenv('RESPONSE_PROBABILITY', 0.05))
QUOTIFY_PROBABILITY = float(os.getenv('QUOTIFY_PROBABILITY', 0.025))
HARDLY_KNOW_HER_PROBABILITY = float(os.getenv('HARDLY_KNOW_HER_PROBABILITY', 0.1))
CALLOUT_PROBABILITY = float(os.getenv('CALLOUT_PROBABILITY', 0.08))
INCLUDE_TEXT_PROBABILITY = float(os.getenv('INCLUDE_TEXT_PROBABILITY', 0.5))
INCLUDE_MEDIA_PROBABILITY = float(os.getenv('INCLUDE_MEDIA_PROBABILITY', 0.5))
INCLUDE_MENTION_PROBABILITY = float(os.getenv('INCLUDE_MENTION_PROBABILITY', 0.5))

logging.basicConfig(level=logging.INFO)

# Cache for group members
members_cache = None
cache_expiry = None
CACHE_DURATION = timedelta(hours=1)
# endregion

# region Member Management
def get_group_members():
    """Fetches group members from GroupMe API with caching."""
    global members_cache, cache_expiry
    
    if members_cache and cache_expiry and datetime.now() < cache_expiry:
        return members_cache
    
    if not GROUP_ID or not ACCESS_TOKEN:
        logging.warning('GROUP_ID and ACCESS_TOKEN required for user tagging')
        return None
    
    try:
        logging.info('Fetching group members from API...')
        response = requests.get(
            f'https://api.groupme.com/v3/groups/{GROUP_ID}/members',
            params={'token': ACCESS_TOKEN}
        )
        
        if response.status_code != 200:
            logging.error(f'GroupMe API Error: {response.status_code}')
            return None
        
        data = response.json()
        if data.get('meta', {}).get('code') != 200:
            logging.error(f'GroupMe API Error: {data.get("meta")}')
            return None
        
        members_cache = data.get('response', {}).get('members', [])
        cache_expiry = datetime.now() + CACHE_DURATION
        
        logging.info(f'Loaded {len(members_cache)} group members')
        return members_cache
        
    except Exception as e:
        logging.error(f'Error fetching group members: {e}')
        return None

def get_random_member():
    """Gets a random group member."""
    members = get_group_members()
    return random.choice(members) if members else None

def get_member_by_id(user_id):
    """Gets member info by user ID."""
    members = get_group_members()
    if not members:
        return None
    
    for member in members:
        if member.get('user_id') == user_id:
            return member
    return None
# endregion

# region File Utilities
def get_random_line_from_file(filename):
    """Returns a random line from a text file."""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        return random.choice(lines) if lines else None
    except Exception as e:
        logging.error(f"Error reading {filename}: {e}")
        return None

def get_random_media(media_type):
    """Returns a random media URL from the specified file."""
    return get_random_line_from_file(f"{media_type}.txt")

def get_random_quote():
    """Returns a random quote from quotes.txt."""
    return get_random_line_from_file('quotes.txt')
# endregion

# region Text Processing
def quotify(text, quotyness):
    """Randomly puts quotes around words in text."""
    if not isinstance(text, str) or not text.strip():
        return None
    
    words = text.split()
    changed = False
    quotified = []
    
    for word in words:
        if random.random() < quotyness:
            changed = True
            quotified.append(f'"{word}"')
        else:
            quotified.append(word)
    
    return ' '.join(quotified) if changed else None

def hardly_know_her(text):
    """Creates 'hardly know her' jokes from words ending in 'er'."""
    if not isinstance(text, str):
        return None
    
    match = re.search(r'(\w+)er\b', text, re.IGNORECASE)
    if match:
        base = match.group(1)
        if match.group(0)[0].isupper():
            base = base.capitalize()
        return f"{base} her? I hardly know her!"
    
    return None
# endregion

# region Message Sending
def send_message(text=None, image_url=None, video_url=None, user_id=None, reply_id=None, extra_attachments=None):
    """Sends a message to GroupMe using the bot API."""
    if not any([text, image_url, video_url, extra_attachments]):
        return None
    
    payload = {'bot_id': BOT_ID, 'text': text or ""}
    attachments = []
    
    if image_url:
        attachments.append({'type': 'image', 'url': image_url})
    
    if video_url and video_url.endswith('.mp4'):
        preview_url = video_url.replace('v.groupme.com', 'i.groupme.com')[:-4] + '.jpg'
        attachments.append({'type': 'video', 'url': video_url, 'preview_url': preview_url})
    
    if user_id:
        member = get_member_by_id(user_id)
        user_name = member.get('nickname', 'user') if member else 'user'
        mention_text = f"@{user_name}"
        payload['text'] = f"{mention_text} {payload['text']}" if payload['text'] else mention_text
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
    
    if extra_attachments:
        attachments.extend(extra_attachments)
    
    if attachments:
        payload['attachments'] = attachments
    
    try:
        # Print what we're about to send
        print(f"📤 SENDING MESSAGE: {payload['text'][:100]}{'...' if len(payload['text']) > 100 else ''}")
        if attachments:
            attachment_types = [att.get('type', 'unknown') for att in attachments]
            print(f"   With attachments: {', '.join(attachment_types)}")
        
        response = requests.post(GROUPME_POST_URL, json=payload)
        logging.info(f"Status: {response.status_code}")
        
        if response.status_code == 202:
            print(f"✅ MESSAGE SENT SUCCESSFULLY")
        else:
            print(f"❌ MESSAGE FAILED: Status {response.status_code}")
            
        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending message: {e}")
        print(f"❌ SEND ERROR: {e}")
        return None
# endregion

# region Message Polling
def get_latest_message():
    """Gets the latest message from the group."""
    try:
        response = requests.get(GROUPME_MESSAGES_URL, params=REQUEST_PARAMS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving messages: {e}")
        return None

def process_message(message):
    """Processes a message and decides whether to respond."""
    if message.get('sender_type') == 'bot':
        return
    
    message_text = message.get('text', '')
    message_id = message.get('id')
    sender_name = message.get('name', 'Unknown')
    
    # Print received message
    print(f"📥 RECEIVED MESSAGE from {sender_name}: {message_text[:100]}{'...' if len(message_text) > 100 else ''}")
    
    # Check for "hardly know her" jokes
    if message_text:
        hkh = hardly_know_her(message_text)
        if hkh and random.random() < HARDLY_KNOW_HER_PROBABILITY:
            print(f"🎭 Responding with 'hardly know her' joke")
            send_message(text=hkh, reply_id=message_id)
            return
    
    # Check for quotify
    if random.random() < QUOTIFY_PROBABILITY and message_text:
        quotified = quotify(message_text, 0.25)
        if quotified:
            print(f"📝 Responding with quotified message")
            send_message(text=quotified, reply_id=message_id)
            return
    
    # Normal random responses
    if random.random() < RESPONSE_PROBABILITY:
        print(f"🎲 Randomly responding to message")
        include_text = random.random() < INCLUDE_TEXT_PROBABILITY
        include_media = random.random() < INCLUDE_MEDIA_PROBABILITY
        include_mention = random.random() < INCLUDE_MENTION_PROBABILITY
        callout_user = random.random() < CALLOUT_PROBABILITY
        
        # Ensure at least one content type
        if not include_text and not include_media:
            if random.random() < 0.5:
                include_text = True
            else:
                include_media = True
        
        text = None
        image_url = None
        video_url = None
        attachments = []
        
        if callout_user:
            # Call out a random user
            random_member = get_random_member()
            if random_member:
                nickname = random_member.get('nickname', 'user')
                user_id = random_member.get('user_id')
                text = f"@{nickname}, I'm calling you out!"
                attachments.append({
                    "type": "mentions",
                    "user_ids": [user_id],
                    "loci": [[0, len(f"@{nickname}")]]
                })
                
                print(f"👀 Calling out user: {nickname}")
                send_message(text=text, reply_id=message_id, extra_attachments=attachments)
                return
        
        # Normal response
        if include_text:
            text = get_random_quote()
        
        if include_media:
            media_type = random.choice(MEDIA_TYPES)
            media_url = get_random_media(media_type)
            if media_type in ['images', 'gifs']:
                image_url = media_url
            else:
                video_url = media_url
        
        mention_user_id = None
        if include_mention:
            random_member = get_random_member()
            mention_user_id = random_member.get('user_id') if random_member else None
        
        if text or image_url or video_url or attachments:
            send_message(
                text=text,
                image_url=image_url,
                video_url=video_url,
                user_id=mention_user_id,
                reply_id=message_id,
                extra_attachments=attachments if attachments else None
            )
    else:
        print(f"🔇 Not responding (random chance)")

def listen_for_messages(response_percentage, pause_interval):
    """Main loop that polls for new messages."""
    last_message_id = None
    last_message_text = None
    
    print(f"🤖 Bot started! Polling every {pause_interval}s with {response_percentage*100}% response rate")
    
    while True:
        last_message = get_latest_message()
        if last_message and 'response' in last_message and 'messages' in last_message['response']:
            message = last_message['response']['messages'][0]
            if last_message_id is None or message['id'] > last_message_id:
                last_message_id = message['id']
                if message['sender_type'] == 'user':
                    current_message_text = message['text']
                    if current_message_text != last_message_text:
                        last_message_text = current_message_text
                        
                        # Override the global RESPONSE_PROBABILITY with the passed parameter
                        global RESPONSE_PROBABILITY
                        original_prob = RESPONSE_PROBABILITY
                        RESPONSE_PROBABILITY = response_percentage
                        
                        process_message(message)
                        
                        # Restore original probability
                        RESPONSE_PROBABILITY = original_prob
                else:
                    print(f"🤖 Ignoring bot message")
        
        time.sleep(pause_interval)
# endregion

# region Entry Point
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python bot.py <response_percentage> <pause_interval>")
        sys.exit(1)
    
    response_percentage = float(sys.argv[1])
    pause_interval = int(sys.argv[2])
    
    logging.info(f'Bot starting with {response_percentage*100}% response rate, {pause_interval}s interval')
    listen_for_messages(response_percentage, pause_interval)
# endregion
