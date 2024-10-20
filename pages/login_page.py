from bs4 import BeautifulSoup
import requests
from .base import Page
from utils.functions import create_session
from utils.captcha import fetch_captcha, get_captcha_data, pick_images, solve_captcha
from data import USER_CREDENTIALS as auth
from config import base

from selenium.webdriver.common.by import By



class LoginPage(Page):
    
    url = base.login_url
    captcha_data = {}
    valid_login_fields = {}
    
    def process(self, context: dict) -> dict:
        username = auth.get('username')
        password = auth.get('password')
        if not (username and password):
            raise Exception('[Login Page]: invalid credentials provided')
        
        if context.get('session'):
            self.session = context['session']
        else:
            self.session = create_session()
        
        if isinstance(self.session, requests.Session):
            response = self.session.get(self.url)
            self.valid_login_fields = self.get_valid_fields(response.text)
            self.captcha_data = fetch_captcha(response.text, self.session)

            captcha = solve_captcha(self.captcha_data, self.session)
            self.captcha_data['captcha'] = captcha
        
            self.login(username, password, with_browser=False)
        else:
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
        return 'availability_page'

    def login(self, username: str, password: str, with_browser=True):
        '''sample response to login endpoint: {
            "success": true,
            "returnUrl": null,
            "IsPasswordChanged": true,
            "IsVerified": true,
            "userId": "3fb39bc6-373c-42d6-b467-6d758b706705",
            "passwordChangeAlert": false
        }'''

        if with_browser:
            self.session.get(self.url)
            self.session.clickable('//button[@id="btnVerify"]')
            
            captcha_data = get_captcha_data(self.session)

            images = pick_images(captcha_data['target'], captcha_data['images'])

            for img_id in images:
                self.session.clickable(f'//div[@id="{img_id}"]')

            self.session.clickable('//button[@type="submit"]')

            input_elements = self.session.driver.find_elements(By.XPATH, '//input[@required]')
            
            for input_element in input_elements:
                label = self.session.driver.find_element(By.XPATH, f'//label[@for="{input_element.get_attribute("id")}"]')
                
                if label and 'Email' in label.text:
                    self.session.send_keys(input_element, "your_email@example.com")
                elif label and 'Password' in label.text:
                    self.session.send_keys(input_element, "your_password")

            self.session.clickable('//button[@type="login"]')


        else:
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
