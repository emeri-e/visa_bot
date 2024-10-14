import requests
from bs4 import BeautifulSoup
import base64

def get_captcha_url(page: str):
    soup = BeautifulSoup(page, "html.parser")

    script = soup.find('script', text=lambda t: 'VerifyRegister' in t).string
    start = script.find("iframeOpenUrl = '") + len("iframeOpenUrl = '")
    end = script.find("';", start)
    captcha_url = script[start:end]
    captcha_url = f"https://ita-pak.blsinternational.com{captcha_url}"
    
    return captcha_url

def get_captcha_data(session, captcha_url):
    response = session.get(captcha_url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract form values
    captcha_form = soup.find('form', {'id': 'captchaForm'})
    captcha_id = captcha_form.find('input', {'id': 'Id'})['value']
    captcha_value = captcha_form.find('input', {'id': 'Captcha'})['value']
    token = captcha_form.find('input', {'name': '__RequestVerificationToken'})['value']

    target_div = soup.find('div', class_='box-label')
    target_number = target_div.get_text().split(' ')[-1]
    
    return {
        'id': captcha_id,
        'captcha': captcha_value,
        '__RequestVerificationToken': token,
        'target': target_number
    }

def get_captcha_images(soup):
    images = soup.find_all('div', class_='captcha-img')
    captcha_images = []

    for img_div in images:
        img_base64 = img_div.find('img')['src'].split(",")[1]
        img_data = base64.b64decode(img_base64)
        img_id = img_div['onclick'].split("'")[1]
        captcha_images.append({
            'id': img_id,
            'image': img_data
        })
    
    return captcha_images

def fetch_captcha(page, session):    
    captcha_url = get_captcha_url(page)
    captcha_data = get_captcha_data(session, captcha_url)

    captcha_page = session.get(captcha_url)
    soup = BeautifulSoup(captcha_page.text, "html.parser")
    captcha_images = get_captcha_images(soup)
    
    captcha_data['images'] = captcha_images
    return captcha_data


def pick_images(target_number, captcha_images):
    selected_images = []
    for img in captcha_images:

        payload = {
            "userid":"john_doe",
            "apikey":"123apikey456123apikey456",
            "data":"/9j/4AAQSkZJRgABAgAAAQAB......"
        }

        requests.post(base.tcaptcha_url, data=payload)
        if target_number == img['id']:
            selected_images.append(img['name'])
    return selected_images

def solve_captcha(captcha_data, session):
    url = "https://ita-pak.blsinternational.com/Global/CaptchaPublic/SubmitCaptcha"

    selected_images = pick_images(captcha_data['target'], captcha_data['images'])

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