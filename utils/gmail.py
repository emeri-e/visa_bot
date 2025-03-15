import os.path
import base64
import re
import time
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _WSGIRequestHandler
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
# import webbrowser
import wsgiref.simple_server
import wsgiref.util
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.common.by import By
# from utils.config import base

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class CustomFlow(InstalledAppFlow):
    def __init__(self, oauth2session, client_type, client_config, redirect_uri=None, code_verifier=None, autogenerate_code_verifier=True):
        super().__init__(oauth2session, client_type, client_config, redirect_uri, code_verifier, autogenerate_code_verifier)

    def webdriver(self):
        """Start webdriver and return state of it."""
        # from selenium.webdriver.common.proxy import Proxy, ProxyType
        options = webdriver.ChromeOptions()

        options.add_argument('--disable-webgl')
        options.add_argument('--disable-canvas-fingerprint')
        # Adding argument to disable the AutomationControlled flag 
        options.add_argument("--disable-blink-features=AutomationControlled") 
        
        # Exclude the collection of enable-automation switches 
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        
        # Turn-off userAutomationExtension 
        options.add_experimental_option("useAutomationExtension", False) 
        

        options.add_argument('--lang=en')  # Set webdriver language to English.
        options.add_argument('log-level=3')  # No logs is printed.
        options.add_argument('--mute-audio')  # Audio is muted.
        # options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        return driver
    
    def run_local_server(self, host="localhost", bind_addr=None, port=8080, authorization_prompt_message=InstalledAppFlow._DEFAULT_AUTH_PROMPT_MESSAGE, success_message=InstalledAppFlow._DEFAULT_WEB_SUCCESS_MESSAGE, open_browser=True, redirect_uri_trailing_slash=True, timeout_seconds=None, token_audience=None, browser=None, **kwargs):

        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            bind_addr or host, port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        redirect_uri_format = (
            "http://{}:{}/" if redirect_uri_trailing_slash else "http://{}:{}"
        )
        self.redirect_uri = redirect_uri_format.format(host, local_server.server_port)
        auth_url, _ = self.authorization_url(**kwargs)

        if open_browser:
            # if browser is None it defaults to default browser
            # webbrowser.get(browser).open(auth_url, new=1, autoraise=True)
            driver = self.webdriver()
            try:
                # Open the target URL
                driver.get(auth_url)

                # Locate the email input field and enter the email
                email_input = WDW(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
                )
                email_input.send_keys('mudassarq16@gmail.com')
                email_input.send_keys(Keys.ENTER)
                time.sleep(3)
                # # Wait for the page to load and locate the "Use another account" link
                # WDW(driver, 10).until(
                #     EC.element_to_be_clickable((By.XPATH, "//div[@class='AsY17b' and text()='Use another account']"))
                # ).click()

                # # Locate the email input field and enter the email
                # email_input = WDW(driver, 10).until(
                #     EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
                # )
                # email_input.send_keys(base._base_email)
                # email_input.send_keys(Keys.ENTER)

                # Wait for the password input field to be present
                password_input = WDW(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
                )
                password_input.send_keys('Pakistan.12')
                time.sleep(3)

                # Click the "Next" button after entering the password
                next_button = WDW(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='button']//span[text()='Next']"))
                )
                next_button.click()
                time.sleep(3)

                continue_button_xpath = "//span[text()='Continue']/ancestor::button"
                WDW(driver, 10).until(EC.element_to_be_clickable((By.XPATH, continue_button_xpath))).click()
                time.sleep(3)
                second_continue_button_xpath = "//span[text()='Continue']/ancestor::button"
                WDW(driver, 10).until(EC.element_to_be_clickable((By.XPATH, second_continue_button_xpath))).click()

                time.sleep(3)

            finally:
                # Close the WebDriver
                pass

        if authorization_prompt_message:
            print(authorization_prompt_message.format(url=auth_url))

        local_server.timeout = timeout_seconds
        local_server.handle_request()

        # Note: using https here because oauthlib is very picky that
        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        self.fetch_token(
            authorization_response=authorization_response, audience=token_audience
        )

        # This closes the socket
        local_server.server_close()

        return self.credentials

class Gmail:
    def __init__(self, email) -> None:
        
        self.email = email
        self.creds = self.__authenticate_gmail()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def confirm(self,bot,email):
        # Replace with the actual email suffix used
        # email_suffix = f'+{username}@gmail.com'

        confirmation_link = self.__get_confirmation_email(email)
        if confirmation_link:
            bot.load_page(confirmation_link)
            return True
        else:
            pass
            

    def __authenticate_gmail(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        token_path = os.path.join('creds',f'{self.email}.json')
        cred_path = os.path.join('creds','credentials.json')
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        cred_path, SCOPES)
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def __get_confirmation_email(self,email):
        # Call the Gmail API
        results = self.service.users().messages().list(userId='me', q='subject:BLS Visa Appointment - Email Verification', maxResults=50).execute()
        messages = results.get('messages', [])

        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = msg['payload']['headers']
            for values in email_data:
                name = values['name']
                if name == 'To' and email in values['value']:
                    msg_str = base64.urlsafe_b64decode(msg['payload']['parts'][1]['body']['data'].encode('ASCII')).decode('utf-8')
                    soup = BeautifulSoup(msg_str, 'html.parser')
                    confirmation_link = soup.find('a', string=re.compile('Confirm your email')).get('href')
                    return confirmation_link
        return None
    
    def confirmation_msgs(self):
        results = self.service.users().messages().list(userId='me', q='subject:Confirm your Pinterest account', maxResults=20).execute()
        messages = results.get('messages', [])

        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            yield msg


    def suspension_msgs(self):
        results = self.service.users().messages().list(userId='me', q='subject:Your Pinterest account has been suspended', maxResults=20).execute()
        messages = results.get('messages', [])

        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            yield msg            
    
    def get_code(self, read: list):
        results = self.service.users().messages().list(userId='me', q='subject:BLS Visa Appointment - Email Verification', maxResults=50).execute()
        messages = results.get('messages', [])

        for message in messages:
            if message['id'] in read:
                continue

            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            msg_str = msg['snippet']

            match = re.search(r'\b\d{6}\b', msg_str)
            if match:
                return match.group(0)
        return None
    
    def fetch_read_msgs(self):
        results = self.service.users().messages().list(userId='me', q='subject:BLS Visa Appointment - Email Verification', maxResults=50).execute()
        messages = results.get('messages', [])
        return [message['id'] for message in messages]
    

if __name__ == '__main__':
    gmail = Gmail()
    read_msgs = gmail.fetch_read_msgs()
    code = gmail.get_code([])