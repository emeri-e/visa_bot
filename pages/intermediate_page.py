import time

from bs4 import BeautifulSoup

from utils.functions import create_session
from utils.models import Browser
from .base import Page


class IntermediatePage(Page):
    url = 'https://ita-pak.blsinternational.com/Global/bls/VisaTypeVerification'

    def __str__(self):
        return 'Intermediate Page'
    def process(self, context):
        session = context['session']

        browser = create_session(with_browser=True)

        #set cookies on browser from session
        for cookie in session.cookies:
            browser.set_cookie(cookie.name, cookie.value)

        response = browser.get(self.url)
        

    def next(self):
        pass
