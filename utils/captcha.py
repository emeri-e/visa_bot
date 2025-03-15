import multiprocessing
import os
import re
import shutil
import time
import requests
from bs4 import BeautifulSoup
from config import base
from ocr.functions import is_ocr_server_running, start_ocr_server, wait_for_server
from utils.exceptions import LoginRedirectException
from utils.functions import create_session
from utils.models import Browser
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.common.by import By
import base64
import cv2
from tqdm import tqdm 
import numpy as np

import easyocr
# reader = easyocr.Reader(['en'], gpu=True)

def get_captcha_url(page: str):
    soup = BeautifulSoup(page, "html.parser")

    # script_text = soup.find('script', text=re.compile(r'VerifyRegister')).string
    try:
        captcha_id = soup.find('input', {'id': 'CaptchaId'})['value']
        script_data = soup.find('input', {'id': 'ScriptData'})['value']
    except:
        captcha_id = None
        script_data = None

    match = re.search(r"iframeOpenUrl\s*=\s*'([^']+)'", page)
    # match2 =re.search(r"iframeOpenUrl\s*=\s*\'([^']+)\'", page)

    # match = match or match2
    if match:
        captcha_url = match.group(1)
        captcha_url = f"https://ita-pak.blsinternational.com{captcha_url}"
    
        return {'captcha_id':captcha_id, 'captcha_url': captcha_url, 'script_data': script_data}
    
    return {}


def get_captcha_data(session, captcha_url=None):
    if isinstance(session, Browser):
        try:
            iframe = WDW(session.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            session.driver.switch_to.frame(iframe)

            WDW(session.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'box-label'))
            )
            
            target_divs = session.driver.find_elements(By.CLASS_NAME, 'box-label')

            highest_z_index = -1
            target_number = None

            for div in target_divs:
                if div.is_displayed():
                    z_index = div.value_of_css_property('z-index')
                    
                    if z_index.isdigit() and int(z_index) > highest_z_index:
                        highest_z_index = int(z_index)
                        target_number = div.text.split(' ')[-1]

            # session.driver.switch_to.default_content()

            WDW(session.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'captcha-img'))
            )
            image_divs = session.driver.find_elements(By.CLASS_NAME, 'captcha-img')
            captcha_images = []

            image_groups = {}

            for img_div in image_divs:
                parent = img_div.find_element(By.XPATH, '..')
                style = parent.get_attribute('style')
                display = parent.value_of_css_property('display')

                if ('display' not in style) and (display == 'block') and img_div.is_displayed():
                    left = int(parent.value_of_css_property('left').replace('px', '').strip())
                    top = int(parent.value_of_css_property('top').replace('px', '').strip())
                    z_index = int(parent.value_of_css_property('z-index'))

                    position_key = (left, top)
                    img_base64 = img_div.get_attribute('src').split(",")[1]  # Extract base64 part
                    img_id = img_div.get_attribute('onclick').split("'")[1]  # Extract image ID
                    
                    if position_key in image_groups:
                        if image_groups[position_key]['z_index'] < z_index:
                            image_groups[position_key] = {
                                'id': img_id,
                                'image': img_base64,
                                'z_index': z_index
                            }
                    else:
                        image_groups[position_key] = {
                            'id': img_id,
                            'image': img_base64,
                            'z_index': z_index
                        }

            captcha_images = [{'id': v['id'], 'image': v['image']} for v in image_groups.values()]


            return {
                'target': target_number,
                'images': captcha_images
            }
        
        except Exception as e:
            print(f"Error: {e}")
            return {'target': None, 'images': []}
    
    #temporary
    # x = create_session(with_browser=True)
    # x.get(captcha_url)

    # text = x.driver.page_source
    for _ in range(10):
        response = session.get(captcha_url)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        
        captcha_form = soup.find('form', {'id': 'captchaForm'})
        if captcha_form:
            break

        time.sleep(0.5)
    else:
        print("Could not fetch captcha form")
        with open('error_captcha_page.html', 'w') as f:
            f.write(text)
        raise LoginRedirectException("Could not fetch captcha form")
    captcha_id = captcha_form.find('input', {'id': 'Id'})['value']
    try:
        captcha_value = captcha_form.find('input', {'id': 'Captcha'})['value']
    except:
        captcha_value = None

    token = captcha_form.find('input', {'name': '__RequestVerificationToken'})['value']

    target_number = get_target_number(text)

    data = {
        'id': captcha_id,
        'captcha': captcha_value,
        '__RequestVerificationToken': token,
        'target': target_number
    }
    
    captcha_images = get_captcha_images(text)
    
    data['images'] = captcha_images

    return data

def get_target_number(text):
    soup = BeautifulSoup(text, "html.parser")

    styles = soup.find_all('style')
    css_styles = {}

    for style in styles:
        rules = style.string.split('}')
        for rule in rules:
            if '{' in rule:
                class_name, properties = rule.split('{')
                class_name = class_name.strip().lstrip('.')
                properties = properties.strip()
                if properties:
                    css_styles[class_name] = properties
    target_divs = soup.find_all('div', class_='box-label')

    highest_z_index = -1
    selected_target_div = None

    for div in target_divs:
        class_list = div.get('class', [])
        if len(class_list) >= 3: 
            z_index_class = class_list[2]  
            z_index_text = css_styles.get(z_index_class, -1)
            z_index = int(z_index_text.replace('z-index:', '').replace(';', '').strip())
            if z_index > highest_z_index:
                highest_z_index = z_index
                selected_target_div = div

    target_number = selected_target_div.get_text().split(' ')[-1]
    return target_number

def get_captcha_images(text):
    soup = BeautifulSoup(text, "html.parser")
    styles = soup.find_all('style')
    css_styles = {}
    
    for style in styles:
        rules = style.string.split('}')
        for rule in rules:
            if '{' in rule:
                class_name, properties = rule.split('{')
                class_name = class_name.strip().lstrip('.')
                properties = properties.strip()
                if properties:
                    css_styles[class_name] = properties

    image_divs = soup.find_all('div', class_='col-4')

    valid_images = []

    for div in image_divs:
        class_list = div.get('class', [])
        styled_classes = [cls for cls in class_list if cls in css_styles]

        if len(styled_classes) == 2:
            img_tag = div.find('img', class_='captcha-img')
            if img_tag:
                img_base64 = img_tag['src'].split(",")[1]  # Extract base64 part
                img_id = img_tag['onclick'].split("'")[1]  # Extract image ID
                valid_images.append({
                    'id': img_id,
                    'image': img_base64
                })

    return valid_images

def fetch_captcha(page, session):    
    captcha_data = get_captcha_url(page)

    captcha_url = captcha_data['captcha_url']   
    x = get_captcha_data(session, captcha_url)
    captcha_data.update(**x)

    return captcha_data


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


# def pick_images(target_number, captcha_images, local = False):
#     if local:
#         return pick_images_local(target_number, captcha_images)
    
#     selected_images = []
#     OCR_API_URL = "http://16.16.24.94:2001/extract/"

#     # Create a directory to save the images if it doesn't already exist
#     save_dir = "saved_images"
#     if os.path.exists(save_dir):
#         shutil.rmtree(save_dir)
#     os.makedirs(save_dir, exist_ok=True)


#     for img in tqdm(captcha_images, desc="Processing Images", unit="image"):
#         image_data = base64.b64decode(img['image'])
#         nparr = np.frombuffer(image_data, np.uint8)
#         decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#         image_path = os.path.join(save_dir, f"{img['id']}.jpg")
#         cv2.imwrite(image_path, decoded_img)

#         _, encoded_img = cv2.imencode('.jpg', decoded_img)
#         image_bytes = encoded_img.tobytes()

#         # Send the image to the FastAPI OCR service
#         response = requests.post(
#             OCR_API_URL,
#             files={"image": ("captcha.jpg", image_bytes, "image/jpeg")}
#         )

#         if response.status_code == 200:
#             text_list = response.json().get("text", [])
#             text = ''.join(text_list)
#             # print(f'{img["id"]} -> {text}')
#             if target_number == text.replace(" ", ""): # or (not text and len(selected_images)<3):
#                 selected_images.append(img['id'])

#     return selected_images


def pick_images(target_number, captcha_images, local=False):
    if local:
        return pick_images_local(target_number, captcha_images)
    
    if not is_ocr_server_running():
        ocr_process = multiprocessing.Process(target=start_ocr_server)
        ocr_process.start()
        wait_for_server()

    selected_images = []
    OCR_API_URL = "http://127.0.0.1:2001/extract/"

    save_images = False  
    save_dir = "saved_images"

    if save_images:
        if os.path.exists(save_dir):
            shutil.rmtree(save_dir)
        os.makedirs(save_dir, exist_ok=True)

    for img in captcha_images: #tqdm(captcha_images, desc="Processing Images", unit="image"):
        image_data = base64.b64decode(img['image'])
        nparr = np.frombuffer(image_data, np.uint8)
        decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        processed_images = preprocess_image(decoded_img)

        for processed_img in processed_images:
            if save_images:
                image_path = os.path.join(save_dir, f"{img['id']}.jpg")
                cv2.imwrite(image_path, processed_img)

            _, encoded_img = cv2.imencode('.jpg', processed_img)
            image_bytes = encoded_img.tobytes()

            response = requests.post(
                OCR_API_URL,
                files={"image": ("captcha.jpg", image_bytes, "image/jpeg")}
            )

            if response.status_code == 200:
                text = response.json().get("text", [])
                # print(text)

                if text:
                    if target_number == text:# or target_number[1:3] == text[1:3] or target_number[0:2] == text[0:2] or (target_number[0]==text[0] and target_number[2]==text[2]):
                        selected_images.append(img['id'])
                    break  

    return selected_images


# def pick_images(target_number, captcha_images):
#     selected_images = []

#     for img in captcha_images:
#         image_data = base64.b64decode(img['image'])
        
#         nparr = np.frombuffer(image_data, np.uint8)
        
#         decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         gray = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2GRAY)
        
#         text = pytesseract.image_to_string(gray, config='--psm 8 digits').strip()
        
#         if target_number == text:
#             selected_images.append(img['id'])
    
#     return selected_images


# def pick_images_local(target_number, captcha_images):
#     reader = easyocr.Reader(['en'], gpu=True)
#     selected_images = []

#     for img in captcha_images:
#         # Decode base64 image string to bytes
#         image_data = base64.b64decode(img['image'])
        
#         # Convert bytes to a NumPy array
#         nparr = np.frombuffer(image_data, np.uint8)
        
#         # Decode image from the NumPy array
#         decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#         # Use EasyOCR to extract digits from the image
#         results = reader.readtext(decoded_img, detail=0)
#         text = ''.join(results).strip()  # Join the result text if there are multiple components
        
#         # If the extracted text matches the target number, add to selected images
#         if target_number == text:
#             selected_images.append(img['id'])
    
#     return selected_images

def preprocess_image(image):
    """Preprocess image using Gaussian/Median Blur + Otsu + Inversion"""

    processed_images = []
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    methods = [
        ("gauss_otsu", False),  # Gaussian + Otsu
        ("median_otsu", False),  # Median + Otsu
        ("gauss_otsu", True),  # Inverted + Gaussian + Otsu
        ("median_otsu", True)   # Inverted + Median + Otsu
    ]

    for method, invert in methods:
        if invert:
            gray = cv2.bitwise_not(gray)

        if method == "gauss_otsu":
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        elif method == "median_otsu":
            blurred = cv2.medianBlur(gray, 5)
        else:
            blurred = gray

        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(binary)

    processed_images.append(image)

    return processed_images

def extract_text(image):
    """Runs OCR on an image and returns extracted text."""
    result = reader.readtext(image, detail=0)
    text = ''.join(result).replace(' ', '').strip()
    return text if text.isdigit() and len(text) == 3 else None

def pick_images_local(target_number, captcha_images):
    global reader

    reader = easyocr.Reader(['en'], gpu=True)

    selected_images = []

    for img in captcha_images:
        # Decode base64 image string to bytes
        image_data = base64.b64decode(img['image'])
        
        # Convert bytes to a NumPy array
        nparr = np.frombuffer(image_data, np.uint8)
        
        # Decode image from the NumPy array
        decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Apply preprocessing
        processed_images = preprocess_image(decoded_img)

        # Check each preprocessed image for OCR match
        for processed_img in processed_images:
            extracted_text = extract_text(processed_img)
            if extracted_text == target_number:
                selected_images.append(img['id'])
                break  # Stop checking once a match is found

    return selected_images

def solve_captcha(captcha_data, session,field='captcha', local = False):
    url = base.captcha_submit_url if field == 'captcha' else 'https://ita-pak.blsinternational.com/Global/NewCaptcha/SubmitCaptcha'

    selected_images = pick_images(captcha_data['target'], captcha_data['images'], local = local)

    # #Test: 
    print('Selected Images: ', selected_images, '\n')
    
    payload = {
        'SelectedImages': ','.join(selected_images),
        'Id': captcha_data['id'],
        '__RequestVerificationToken': captcha_data['__RequestVerificationToken'],
        'X-Requested-With': 'XMLHttpRequest'
    }
    if field == 'captcha':
        payload['Captcha'] = captcha_data['captcha']

    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = session.post(url, data=payload) #, headers=headers)

    result = response.json()

    if result.get('success') == False:
        return None
    elif result.get('success') == True:
        return result[field]
    else:
        return None