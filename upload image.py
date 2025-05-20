import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

url = 'https://image.groupme.com/pictures'
headers = {
    'X-Access-Token': os.getenv('ACCESS_TOKEN'),
    'Content-Type': 'image'
}

def upload_image(image_path):
    try:
        with open(image_path, 'rb') as image_file:
            response = requests.post(url, headers=headers, data=image_file)
            response.raise_for_status()
            image_url = response.json()['payload']['url']
            print(f"Image uploaded: {image_url}")
            return image_url
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image: {e}")
        return None
    
def upload_image_from_url(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_path = 'temp.jpg'
        with open(image_path, 'wb') as image_file:
            image_file.write(response.content)
        return upload_image(image_path)
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image from URL: {e}")
        return None

def upload_folder(folder_path):
    for file_name in os.listdir(folder_path):
        image_path = os.path.join(folder_path, file_name)
        image_url = upload_image(image_path)
        if image_url:
            append_to_file("uploaded images.txt", image_url)

def append_to_file(file_path, text):
    with open(file_path, 'a') as file:
        file.writeline(text + '\n')

if __name__ == '__main__':
    print("1. Upload an image from file")
    print("2. Upload an image from url")
    print("3. Upload an images from folder")
    choice = input("Enter your choice: ")
    if choice == '1':
        image_path = input("Enter the path of the image you want to upload: ")
        image_url = upload_image(image_path)
        if image_url:
            append_to_file('uploaded images.txt', image_url)
    elif choice == '2':
        image_url = input("Enter the URL of the image you want to upload: ")
        image_url = upload_image_from_url(image_url)
        if image_url:
            append_to_file('uploaded images.txt', image_url)
    elif choice == '3':
        folder_path = input("Enter the path of the folder containing images you want to upload: ")
        upload_folder(folder_path)
    input("Press Enter to exit...")
