import re
import requests
from bs4 import BeautifulSoup
from config import base
from utils.models import Browser
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.common.by import By
import base64
import cv2
import pytesseract
# import easyocr
import numpy as np

def get_captcha_url(page: str):
    soup = BeautifulSoup(page, "html.parser")

    script_text = soup.find('script', text=re.compile(r'VerifyRegister')).string
    captcha_id = soup.find('input', {'id': 'CaptchaId'})['value']
    script_data = soup.find('input', {'id': 'ScriptData'})['value']

    match = re.search(r"iframeOpenUrl\s*=\s*'([^']+)'", script_text)
    
    if match and captcha_id:
        captcha_url = match.group(1)
        captcha_url = f"https://ita-pak.blsinternational.com{captcha_url}"
    
        # return captcha_url
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
    
    response = session.get(captcha_url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    captcha_form = soup.find('form', {'id': 'captchaForm'})
    captcha_id = captcha_form.find('input', {'id': 'Id'})['value']
    captcha_value = captcha_form.find('input', {'id': 'Captcha'})['value']
    token = captcha_form.find('input', {'name': '__RequestVerificationToken'})['value']

    # TODO: it needs to select the actual target maybe based on visiblity
    # it just selects the first one here
    target_div = soup.find('div', class_='box-label')
    target_number = target_div.get_text().split(' ')[-1]
    
    return {
        'id': captcha_id,
        'captcha': captcha_value,
        '__RequestVerificationToken': token,
        'target': target_number
    }

def get_captcha_images(soup):
    # TODO: this fetches all available images. instead of the visible 9 images
    images = soup.find_all('img', class_='captcha-img')
    captcha_images = []

    for img_div in images:
        img_base64 = img_div['src'].split(",")[1]
        img_id = img_div['onclick'].split("'")[1]
        captcha_images.append({
            'id': img_id,
            'image': img_base64
        })
    return captcha_images

def fetch_captcha(page, session):    
    captcha_data = get_captcha_url(page)

    captcha_url = captcha_data['captcha_url']   
    x = get_captcha_data(session, captcha_url)
    captcha_data.update(**x)

    captcha_page = session.get(captcha_url)
    soup = BeautifulSoup(captcha_page.text, "html.parser")
    captcha_images = get_captcha_images(soup)
    
    captcha_data['images'] = captcha_images
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


def pick_images(target_number, captcha_images):
    selected_images = []

    for img in captcha_images:
        image_data = base64.b64decode(img['image'])
        
        nparr = np.frombuffer(image_data, np.uint8)
        
        decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        gray = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2GRAY)
        
        text = pytesseract.image_to_string(gray, config='--psm 8 digits').strip()
        
        if target_number == text:
            selected_images.append(img['id'])
    
    return selected_images

# def pick_images(target_number, captcha_images):
#     reader = easyocr.Reader(['en'])  # Initialize EasyOCR reader
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

def solve_captcha(captcha_data, session):
    url = base.captcha_submit_url

    selected_images = pick_images(captcha_data['target'], captcha_data['images'])

    # #Test: 
    # selected_images = ['gikxkrr','tdlbgu','swqrd']
    payload = {
        'SelectedImages': ','.join(selected_images),
        'Id': captcha_data['id'],
        'Captcha': captcha_data['captcha'],
        '__RequestVerificationToken': captcha_data['__RequestVerificationToken']
    }

    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }

    response = session.post(url, data=payload, headers=headers)

    result = response.json()

    if result.get('status') == True:
        return captcha_data['captcha']
    else:
        return None