import time

from bs4 import BeautifulSoup
from .base import Page
from forms import AvailabilityForm
from utils.captcha import fetch_captcha, solve_captcha
from data import AVAILABILITY_FIELDS


class AvailabilityPage(Page):
    url = 'https://ita-pak.blsinternational.com/Global/bls/VisaTypeVerification'

    def process(self, context):
        session = context['session']
        response = session.get(self.url)
        form = AvailabilityForm(value=AVAILABILITY_FIELDS)

        data = form.validated_data

        page_ctx = self.get_page_context(context)

        headers = {
            'X-Requested-With': 'XMLHttpRequest'
        }

        while True:
            # search availability
            data.update(page_ctx)
            res = session.post(self.url, data=data, headers=headers)

            time.sleep(10)


    def get_page_context(self, context):
        session = context['session']
        res = session.get(self.url)

        captcha_data = fetch_captcha(res.text, self.session)
        captcha = solve_captcha(self.captcha_data, self.session)
        ctx = {
            'CaptchaId': captcha_data['captcha_id'],
            'CaptchaData': captcha,
            'ScriptData': captcha_data['script_data'],
            '__RequestVerificationToken': captcha_data['__RequestVerificationToken']
        }

        # return page context data
        return ctx

    def next(self):
        pass
