from .base import Page
from utils.functions import create_session
from utils.captcha import fetch_captcha, solve_captcha
from data import USER_CREDENTIALS as auth
from config import base


class LoginPage(Page):
    url = base.login_url
    
    def process(self, context: dict) -> dict:
        username = auth.get('username')
        password = auth.get('password')
        if not (username and password):
            raise Exception('[Login Page]: invalid credentials provided')
        
        session = create_session()
        
        response = session.get(self.url)
        captcha_data = fetch_captcha(response.text, session)

        captcha = solve_captcha(captcha_data, session)
        
        self.login(username, password)
        
        context.update(session=session)
        return context
    
    def next(self):
        return ''

    def login(self, username: str, password: str):
        return
