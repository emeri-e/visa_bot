from .base import Page
from data import AVAILABILITY_FIELDS as av


class BookingForm:
    _data = {}
    _validated = False
    errors = {}

    def is_valid(self):
        if all([

        ]):
            self._validated = True

        return self._validated

    def validated_data(self):
        if self._validated:
            return self._data
        raise Exception('form not validated')

    def validate_category(self):
        cat = av.get('category')
        if cat in ['']:
            self._data['category'] = cat
            return cat
        self.errors['category'] = f'invalid value: {cat}'

    def validate_location(self):
        location = av.get('location')
        if location in []:
            self._data['location'] = location
            return location
        self.errors['location'] = f'invalid value: {location}'

    def validate_visa_type(self):
        vt = av.get('visa_type')
        if vt in []:
            self._data['visa_type'] = vt
            return vt
        self.errors['visa_type'] = f'invalid value: {vt}'

    def validate_visa_subtype(self):
        vt = av.get('visa_subtype')
        if vt in []:
            self._data['visa_subtype'] = vt
            return vt
        self.errors['visa_subtype'] = f'invalid value: {vt}'


class BookingPage(Page):
    url = 'https://ita-pak.blsinternational.com/Global/bls/VisaTypeVerification'

    def process(self, context):
        session = context['session']
        response = session.get(self.url)
        captcha_data = fetch_captcha(response.text, session)

        captcha = solve_captcha(captcha_data, session)

        pass

    def next(self):
        pass

    def validate_form(self):

        return {}