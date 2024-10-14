import requests

from utils.captcha import fetch_captcha, solve_captcha

def create_session():
    session = requests.Session()
    proxy = "http://spoah8u2pq:gkeF46R1z=R3vVummx@pk.smartproxy.com:10001"
    session.proxies = {
        'http': proxy,
        'https': proxy
    }
    return session

def login(username, password):
    session = create_session()

    url = "https://ita-pak.blsinternational.com/Global/Account/LogIn"
    response = session.get(url)

    captcha_data = fetch_captcha(response.text, session)

    captcha = solve_captcha(captcha_data, session)

    # proceed to login with captcha and return session


