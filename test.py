import requests
from config import base
import base64
import cv2
import pytesseract
import numpy as np

# def pick_images(target_number, captcha_images):
#     selected_images = []
#     for img in captcha_images:

#         payload = {
#             "userid":base.tcaptcha_username,
#             "apikey":base.tcaptcha_apikey,
#             "data":img['image']
#         }

#         # TODO: this aways returns 503: "name \'resp\' is not defined"
#         res = requests.post(base.tcaptcha_url, data=payload)
#         if res.status_code == 200:
#             text = res.json()['result']
#             if target_number == text:
#                 selected_images.append(img['id'])
#     return selected_images

def pick_images(target_number, captcha_images):
    selected_images = []

    for img in captcha_images:
        try:
            # Decode base64 image string to bytes
            image_data = base64.b64decode(img['image'])
            
            # Convert bytes to a NumPy array
            nparr = np.frombuffer(image_data, np.uint8)
            
            # Decode image from the NumPy array
            decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Check if the image was successfully decoded
            if decoded_img is None:
                print(f"Warning: Failed to decode image with ID: {img['id']}")
                continue  # Skip to the next image if decoding failed
            
            # Convert the image to grayscale
            gray = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2GRAY)
            
            # Use pytesseract to extract digits from the image
            text = pytesseract.image_to_string(gray, config='--psm 8 digits').strip()
            
            # If the extracted text matches the target number, add to selected images
            if target_number == text:
                selected_images.append(img['id'])

        except Exception as e:
            # Handle any other exceptions and continue
            print(f"Error processing image with ID: {img['id']}. Exception: {e}")
            continue
    
    return selected_images


data = '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'

  
imgs = [{'id':'hyehw', 'image':data},]

target_number = '1234'

selected_images = pick_images(target_number, imgs)