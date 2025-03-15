

import logging
import os
from utils.captcha import fetch_captcha, solve_captcha

log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'main.log')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class Page:
    '''this interface is implemented by every page
    :process: this method is called to process the page.
        it should take only one parameter, context which contains all
        the current state of the application needed to process the page.
        it should return the current state of the application as context.
        
    :next: this method is called after processing a page to return the url or
        identifier for the next page
    
    NOTE: the seperation of page should make it possible that given the right context,
        the page will always process successfully.
        this will also help in unit testing the application page by page.
    '''
    
    def __init__(self, logger = logger) -> None:
        # self.url = ''
        self.session = None
        self.logger = logger
    
    def process(self, context: dict) -> dict:
        raise NotImplementedError
    
    def next(self) -> str:
        raise NotImplementedError

    def process_captcha(self, page_text, captcha_field_name='captcha', use_local_ocr=False, retry_count=1) -> dict:
        
        print(f'[{str(self)}]: fetching captcha....')
        self.valid_login_fields = self.get_valid_fields(page_text)
        self.captcha_data = fetch_captcha(page_text, self.session)
        # print('done.')
        print('Target Number: ', self.captcha_data['target'])

        print(f'[{str(self)}]: solving captcha....')
        captcha = solve_captcha(self.captcha_data, self.session, captcha_field_name, local=use_local_ocr)
        if captcha: 
            self.captcha_data['captcha'] = captcha
            print(f'captcha solved in {retry_count} attempts.')

            return self.captcha_data
        else:
            print(f'[{str(self)}]: processing captcha failed. retrying...')
            return self.process_captcha(page_text, captcha_field_name, use_local_ocr, retry_count + 1)
