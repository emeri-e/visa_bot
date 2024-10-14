import re
import requests
from bs4 import BeautifulSoup
from config import base

def get_captcha_url(page: str):
    soup = BeautifulSoup(page, "html.parser")

    script_text = soup.find('script', text=re.compile(r'VerifyRegister')).string

    match = re.search(r"iframeOpenUrl\s*=\s*'([^']+)'", script_text)
    
    if match:
        captcha_url = match.group(1)
        captcha_url = f"https://ita-pak.blsinternational.com{captcha_url}"
    
        return captcha_url
    
    return None

def get_captcha_data(session, captcha_url):
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
    #TODO: this fetches all available images. instead of the visible 9 images
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
            "userid":base.tcaptcha_username,
            "apikey":base.tcaptcha_apikey,
            "data":img['image']
        }

        #TODO: this aways returns 503: "name \'resp\' is not defined"
        res = requests.post(base.tcaptcha_url, data=payload)
        if res.status_code == 200:
            text = res.json()['result']
            if target_number == text:
                selected_images.append(img['id'])
    return selected_images

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