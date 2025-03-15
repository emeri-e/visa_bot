import json
import re
import requests

from config import base
from utils.models import Browser, CustomSession

def create_session(with_browser=False, with_proxy=True):

    if with_browser:
        if with_proxy:
            return Browser(proxy={'host': base.proxy_ip, 'port': base.proxy_port, 'username': base.proxy_user, 'password': base.proxy_password})
        else:
            return Browser()
    
    session = CustomSession()
    if with_proxy:
        proxy = base.proxy
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
        
    session.trust_env = False
    session.headers.update({
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://ita-pak.blsinternational.com',
                'Priority': 'u=1, i',
                'Referer': 'https://ita-pak.blsinternational.com/Global/account/login',
                'Sec-CH-UA': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Linux"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'
            })
    return session

def extract_json(page_text, key):
    cleaned_text = re.sub(r'\\n|\\t', '', page_text)  
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  

    pattern = rf"var\s+{key}\s*=\s*(\[\s*.*?\]);"
    match = re.search(pattern, cleaned_text)

    if match:
        json_text = match.group(1)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for key: {key}")
    return None

def extract_applicant(page_text, key):
    cleaned_text = re.sub(r'\\n|\\t', '', page_text)  
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  

    pattern = r"var\s+primaryApplicant\s*=\s*({\s*.*?});"
    match = re.search(pattern, cleaned_text)

    if match:
        json_text = match.group(1)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for key: {key}")
    return None