from bs4 import BeautifulSoup
from .base import Page
from utils.functions import create_session
from utils.captcha import fetch_captcha, solve_captcha
from data import USER_CREDENTIALS as auth
from config import base


class LoginPage(Page):
    
    url = base.login_url
    captcha_data = {}
    valid_login_fields = {}
    
    def process(self, context: dict) -> dict:
        username = auth.get('username')
        password = auth.get('password')
        if not (username and password):
            raise Exception('[Login Page]: invalid credentials provided')
        
        self.session = create_session()
        
        response = self.session.get(self.url)
        self.valid_login_fields = self.get_valid_fields(response.text)
        self.captcha_data = fetch_captcha(response.text, self.session)

        captcha = solve_captcha(self.captcha_data, self.session)
        self.captcha_data['captcha'] = captcha
        
        self.login(username, password)
        
        context.update(session=self.session)
        return context
    
    def get_valid_fields(self, page_text):
        soup = BeautifulSoup(page_text, 'html.parser')
        result = {'username_field': '', 'password_field': ''}

        input_elements = soup.find_all('input', required=True)

        for input_element in input_elements:
            label = soup.find('label', attrs={'for': input_element['id']})
            
            if label and 'Email' in label.text:
                result['username_field'] = input_element['id']
            elif label and 'Password' in label.text:
                result['password_field'] = input_element['id']

        return result
      
    def next(self):
        return ''

    def login(self, username: str, password: str):
        '''sample response to login endpoint: {
            "success": true,
            "returnUrl": null,
            "IsPasswordChanged": true,
            "IsVerified": true,
            "userId": "3fb39bc6-373c-42d6-b467-6d758b706705",
            "passwordChangeAlert": false
        }'''
        payload = {
            self.valid_login_fields['username_field']: username,
            self.valid_login_fields['password_field']: password,
            'CaptchaId': self.captcha_data['captcha_id'],
            'CaptchaData': self.captcha_data['captcha'],
            'ScriptData': self.captcha_data['script_data'],
            '__RequestVerificationToken': self.captcha_data['__RequestVerificationToken']
        }

        headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }

        response = self.session.post(self.url, data=payload, headers=headers)

        result = response.json()

        if result.get('status') == True:
            return True
        else:
            return None
