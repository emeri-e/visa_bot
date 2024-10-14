import requests

from utils.captcha import fetch_captcha, solve_captcha
from config import base

def create_session():
    session = requests.Session()
    proxy = base.proxy
    session.proxies = {
        'http': proxy,
        'https': proxy
    }
    return session

def login(username, password):
    session = create_session()

    url = base.login_url
    response = session.get(url)

    captcha_data = fetch_captcha(response.text, session)

    captcha = solve_captcha(captcha_data, session)

    # proceed to login with captcha and return session


