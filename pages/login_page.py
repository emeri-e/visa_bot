from bs4 import BeautifulSoup
import requests
from .base import Page
from utils.functions import create_session
from utils.captcha import fetch_captcha, get_captcha_data, pick_images, solve_captcha
from config import base

from selenium.webdriver.common.by import By



class LoginPage(Page):
    
    url = base.login_url
    captcha_data = {}
    valid_login_fields = {}

    def __str__(self):
        return 'Login'
    
    def process(self, context: dict) -> dict:
        username = context.get('username')
        password = context.get('password')
        if not (username and password):
            raise Exception('[Login Page]: invalid credentials provided')
        
        # if context.get('session'):
        #     self.session = context['session']
        # else:
        # print('[Login]: creating new session...')
        self.session = create_session(with_proxy = context.get('use_proxy'))
        
        if isinstance(self.session, requests.Session):
            # print('[Login]: CLI session created')
            response = self.session.get(self.url)
            print('[Login]: started...')
            self.captcha_data = self.process_captcha(response.text, use_local_ocr=context.get('local_ocr'))

            print('[Login]: logging in...')
            status =self.login(username, password, with_browser=False)
        
        else:
            status = self.login(username, password)
        
        if status == True:
            print('[Login]: login successful\n\n')
            context.update(session=self.session)
            return context
        
        else:
            raise Exception(f'[Login]: login failed with the response: {status}')
    
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

        token = soup.find('input', {'name': '__RequestVerificationToken'})['value']

        result['__RequestVerificationToken'] = token
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

            self.session.clickable('//i[@id="submit"]')

            input_elements = self.session.driver.find_elements(By.XPATH, '//input[@required]')
            
            for input_element in input_elements:
                label = self.session.driver.find_element(By.XPATH, f'//label[@for="{input_element.get_attribute("id")}"]')
                
                if label and 'Email' in label.text:
                    self.session.send_keys(input_element, username)
                elif label and 'Password' in label.text:
                    self.session.send_keys(input_element, password)

            self.session.clickable('//button[@id="btnSubmit"]')


        else:
            payload = {
                'UserId1': '',
                'UserId2': '',
                'UserId3': '',
                'UserId4': '',
                'UserId5': '',
                'UserId6': '',
                'UserId7': '',
                'UserId8': '',
                'UserId9': '',
                'UserId10': '',
                'Password1': '',
                'Password2': '',
                'Password3': '',
                'Password4': '',
                'Password5': '',
                'Password6': '',
                'Password7': '',
                'Password8': '',
                'Password9': '',
                'Password10': '',
                'ReturnUrl': '',
                'CaptchaParam': ''
            }

            additional_fields = {
                self.valid_login_fields['username_field']: username,
                self.valid_login_fields['password_field']: password,
                'CaptchaId': self.captcha_data['captcha_id'],
                'CaptchaData': self.captcha_data['captcha'],
                'ScriptData': self.captcha_data['script_data'],
                '__RequestVerificationToken': self.valid_login_fields['__RequestVerificationToken']
            }
            print(f"Sending login data: {additional_fields}")

            payload.update(additional_fields)

            self.session.headers.update({
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


            response = self.session.post(self.url, data=payload)
            
            # with open('response.html', 'w') as f:
            #     f.write(response.text)

            result = response.json()
            

            if result.get('success') == True:
                return True
            else:
                return result
