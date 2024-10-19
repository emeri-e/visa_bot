import requests

from utils.captcha import fetch_captcha, solve_captcha
from config import base
from utils.models import Browser

def create_session(with_browser=True):

    if with_browser:
        return Browser(proxy={'host': base.proxy_ip, 'port': base.proxy_port, 'username': base.proxy_user, 'password': base.proxy_password})
    
    session = requests.Session()
    proxy = base.proxy
    session.proxies = {
        'http': proxy,
        'https': proxy
    }
    session.trust_env = False
    return session

def login(username, password):
    session = create_session()

    url = base.login_url
    response = session.get(url)

    captcha_data = fetch_captcha(response.text, session)

    captcha = solve_captcha(captcha_data, session)

    # proceed to login with captcha and return session
