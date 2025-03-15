import random
import time

from bs4 import BeautifulSoup

# from utils.functions import create_session
# from utils.models import Browser
from .base import Page
# from utils.functions import extract_json
from requests_toolbelt.multipart.encoder import MultipartEncoder


import json
import re


class DetailsPage(Page):
    url = None

    def __str__(self):
        return 'Creating appointment'

    def process(self, context):
        self.session = context['session']
        self.url = f"https://ita-pak.blsinternational.com{context['returnUrl']}"

        context['Referer'] = self.url
        response = self.session.get(self.url)
        
        html_response = response.text
        # "Your previous payment request is still under processing. Please wait 7 minute(s) to confirm the payment."
        if 'You have already initiated an appointment which is not completed' in html_response:
            match = re.search(r'after (\d+) minute', html_response)
            if match:
                wait_time = int(match.group(1))  # Extracted wait time in minutes
            else:
                wait_time = 1  # Default wait time in minutes if extraction fails
            
            print(f"You have already initiated an appointment which is not completed. Waiting for {wait_time} minute(s).")
            time.sleep(wait_time * 60)  # Convert minutes to seconds and wait

            return self.process(context)
        
        if 'Your previous payment request is still under processing' in html_response:
            match = re.search(r'wait (\d+) minute', html_response)
            if match:
                wait_time = int(match.group(1))  # Extracted wait time in minutes
            else:
                wait_time = 1  # Default wait time in minutes if extraction fails
            
            print(f"Previous payment request is still under processing. Waiting for {wait_time} minute(s).")
            time.sleep(wait_time * 60)  # Convert minutes to seconds and wait

            return self.process(context)
        
        self.valid_fields = self.get_valid_fields(html_response)

        self.captcha_data = self.process_captcha(html_response, use_local_ocr=context.get('local_ocr'))
        avail_dates = self._extract_avail_dates(html_response)
        random.shuffle(avail_dates)
        
        self.context = context

        if avail_dates:
            for date in avail_dates:
                # if context.get('allowed_dates') and date not in context['allowed_dates']:
                #     continue
                time_slots = self._fetch_time_slots(date, context['choices'])

                if time_slots:
                    slot = random.choice(time_slots)
                    email_code = self.verify_email(context['gmail'])
                    image_file_id = self._upload_profile_image(context['image_file_path'])

                    if not (email_code and image_file_id):
                        raise Exception("Failed to verify email or upload passport")
                    
                    context['ApplicantPhotoId'] = image_file_id
                    context['email_code'] = email_code

                    appointment_id = self._process_booking( date, slot, context)

                    if appointment_id:
                        context['appointment_id'] = appointment_id
                        context['appointment_rvt'] = self.valid_fields['__RequestVerificationToken']
                        return context
                    
                    context['next_page'] = 'availability_page'
                    return context
    def _extract_avail_dates(self, html_response):
        cleaned_text = re.sub(r'\\n|\\t', '', html_response)  
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        match = re.search(r'var availDates =(.*?);', cleaned_text)
        if match:
            dates_data = json.loads(match.group(1))
            available_dates = [
                date_entry["DateText"]
                for date_entry in dates_data.get("ad", [])
                if date_entry["SingleSlotAvailable"]
            ]
            
            return available_dates
        return []

    def _fetch_time_slots(self, date, choices):
        url = "https://ita-pak.blsinternational.com/Global/blsappointment/GetAvailableSlotsByDate"
        payload = {
            "appointmentDate": date,
            "locationId": choices['locationId'],
            "categoryId": choices['categoryId'],
            "visaType": choices['visaType'],
            "visaSubType": choices['visaSubType'],
            "applicantCount": 1,
            "dataSource": "WEB_BLS",
            "missionId": choices['missionId']
        }

        headers = {
            "requestverificationtoken": self.valid_fields['__RequestVerificationToken']
        }
        response = self.session.post(url, headers=headers, data=payload)
        data = response.json()

        slots = [slot['Name'] for slot in data if int(slot['Count']) > 0]

        return slots
    

    def _process_booking(self, date, time_slot, context):
        

        url = "https://ita-pak.blsinternational.com/Global/BLSAppointment/ManageAppointment"
        payload = {
            f"AppointmentDate{self.valid_fields['date_slot_id']}": date,
            f"AppointmentSlot{self.valid_fields['date_slot_id']}": time_slot,
            "ApplicantsNo": 1,

            "MobileCountryCode": self.valid_fields['MobileCountryCode'],
            "Mobile": self.valid_fields['Mobile'],
            "Email": self.valid_fields['Email'],
            "EmailVerificationCode": context['email_code'],
            "CaptchaData": self.captcha_data['captcha'],
            "CaptchaId": self.valid_fields['CaptchaId'],
            "CaptchaData2": self.valid_fields['CaptchaData2'],

            "EmailCode": self.valid_fields['EmailCode'],
            "MobileCode": self.valid_fields['MobileCode'],
            "Id": self.valid_fields['Id'],
            "ScriptData": self.valid_fields['script_data'],


            "MissionId": context['choices']['missionId'],
            "LocationId": context['choices']['locationId'],
            "VisaType": context['choices']['visaType'],
            "VisaSubTypeId": context['choices']['visaSubType'],
            "AppointmentCategoryId": context['choices']['categoryId'],
  
            "DataAction": "Create",
            "ApplicantPhotoId": context['ApplicantPhotoId'],
            "AppointmentDetailsList": "[]",
            "MaximumAllowedDays": "0",
            "SaveState": "Appointment",
            "EmailVerified": "True",
            "MobileVerified": "False",
            "DataSource": "WEB_BLS",
            "AppointmentFor": "Individual",
            "ServerAppointmentDate": date,

            "MobileVerificationCode": '',
            "AppointmentId": '',
            "ImageId": '',
            "nextSectionId": '',
            "FullSlot": '',
            "Holidays": '',
            "WeekDays": '',
            "AppointmentNo": '',
            "JurisdictionId": '',
            "PassportJurisdictionId": '',
            "ResidenceJurisdictionId": '',
            "ResidenceDurationOfStayId": '',
            "TravelDate": '',
            
            "__RequestVerificationToken": self.valid_fields.get("__RequestVerificationToken"),
            "X-Requested-With": "XMLHttpRequest",
        }
        # with open('detail.json', 'w') as f:
        #     json.dump(payload, f, indent=4)
        print("Creating appointment...")

        response = self.session.post(url, data=payload)
        data = response.json()

        if data['success']:
            print(f"Appointment created for {date} at {time_slot}. Details: {data}")

            # with open('detail_response.json', 'w') as f:
            #     json.dump(payload, f, indent=4)
            return data['model']['Id']
        else:
            print("Appointment creation failed!")
            self.logger.warning(f'Appointment failed to create with the response: {data}')

    def get_valid_fields(self, page_text):
        soup = BeautifulSoup(page_text, 'html.parser')
        result = {'username_field': '', 'password_field': ''}

        date_slot_id = self.get_visible_id(page_text, 'AppointmentDate')
        MobileCountryCode = soup.find('input', {'id': 'MobileCountryCode'})['value']
        Mobile = soup.find('input', {'id': 'Mobile'})['value']
        Email = soup.find('input', {'id': 'Email'})['value']

        token = soup.find('input', {'name': '__RequestVerificationToken'})['value']
        script_data = soup.find('input', {'id': 'ScriptData'})['value']
        email_code = soup.find('input', {'id': 'EmailCode'})['value']
        mobile_code = soup.find('input', {'id': 'MobileCode'})['value']
        email_id = soup.find('input', {'id': 'Id'})['value']
        CaptchaData2 = soup.find('input', {'id': 'CaptchaData2'})['value']
        CaptchaId = soup.find('input', {'id': 'CaptchaId'})['value']
        
        result['__RequestVerificationToken'] = token
        result['script_data'] = script_data
        result['EmailCode'] = email_code
        result['MobileCode'] = mobile_code
        result['Id'] = email_id
        result['CaptchaData2'] = CaptchaData2
        result['CaptchaId'] = CaptchaId

        result['MobileCountryCode'] = MobileCountryCode
        result['Mobile'] = Mobile
        result['Email'] = Email
        result['date_slot_id'] = date_slot_id
        

        return result
    
    def next(self):
        return 'form_page'
    
    def get_visible_id(self, text, item):
            soup = BeautifulSoup(text, "html.parser")
            styles = soup.find_all('style')
            css_styles = {}

            for style in styles:
                if style.string:
                    rules = style.string.split('}')
                    for rule in rules:
                        if '{' in rule: 
                            class_name, properties = rule.split('{')
                            class_name = class_name.strip().lstrip('.')
                            properties = properties.strip()
                            if properties:
                                css_styles[class_name] = properties

            divs = soup.find_all('div', class_='col-md-3')
            valid_divs = []

            for div in divs:
                label = div.find('input') #, id=lambda x: x and item in x)
                if item not in div.prettify():
                    continue

                class_list = div.get('class', [])
                styled_classes = [cls for cls in class_list if cls in css_styles]

                for styled_class in styled_classes:
                    if 'display: block' in css_styles.get(styled_class, '') or  'display:block' in css_styles.get(styled_class, ''):
                        location_id = label.get('id')
                        if location_id and item in location_id:
                            valid_divs.append(location_id.replace(item, ''))
                        # break

            return valid_divs[0]
    
    
    def verify_email(self, gmail):
        # url = "https://ita-pak.blsinternational.com/Global/blsappointment/SendAppointmentVerificationCode"

        # payload = {
        #     "code": self.valid_fields['EmailCode'],
        # }

        # r = self.session.get(url, data=payload)

        # #manual
        # url = "https://ita-pak.blsinternational.com/Global/blsappointment/VerifyEmail"
        # code = input("Enter code: ")
        # payload = {
        #     "Code": code,
        #     "Value": self.valid_fields['EmailCode'],
        #     "Id": self.valid_fields['Id']
        # }
        
        # headers = {
        #     "requestverificationtoken": self.valid_fields['__RequestVerificationToken']
        # }

        # r = self.session.post(url, data=payload, headers=headers)
        # data = r.json()
        # if data['success']:
        #     print("Email verified!")
        #     return True

        # raise Exception("Failed to verify email")
        ####

        url = "https://ita-pak.blsinternational.com/Global/blsappointment/SendAppointmentVerificationCode"

        payload = {
            "code": self.valid_fields['EmailCode'],
        }
        read_msgs = gmail.fetch_read_msgs()
    
        r = self.session.get(url, data=payload)
        if r.status_code == 200:
            while True:
                code = gmail.get_code(read_msgs)
                
                if code:
                    print(f'Email code received: {code}')

                    url = "https://ita-pak.blsinternational.com/Global/blsappointment/VerifyEmail"

                    payload = {
                        "Code": code,
                        "Value": self.valid_fields['EmailCode'],
                        "Id": self.valid_fields['Id']
                    }
                    
                    headers = {
                        "requestverificationtoken": self.valid_fields['__RequestVerificationToken']
                    }
                    
                    r = self.session.post(url, data=payload, headers=headers)
                    data = r.json()
                    if data['success']:
                        print("Email verified!")
                        return code

                    raise Exception("Failed to verify email")
                else:
                    time.sleep(5)



    def _upload_profile_image(self, file_path):
        url = "https://ita-pak.blsinternational.com/Global/query/UploadProfileImage"
        with open(file_path, "rb") as file:
            # Construct the multipart form-data
            encoder = MultipartEncoder(
                fields={
                    "file": ("filename", file, "application/octet-stream"),
                }
            )
            headers = {
                "Content-Type": encoder.content_type,  # Automatically sets the boundary
                "requestverificationtoken": self.session.cookies.get("__RequestVerificationToken"),
            }
            # Make the POST request with the multipart data
            response = self.session.post(url, headers=headers, data=encoder)
            if response.status_code == 415:
                raise Exception("Unsupported Media Type: Check the format and headers.")
            elif response.status_code != 200:
                raise Exception(f"Failed to upload profile image: {response.status_code} {response.text}")

            # Parse the JSON response
            data = response.json()
            if data.get("success"):
                print("Profile image uploaded successfully.")
                return data.get("fileId")
            else:
                raise Exception("Failed to upload profile image: Server returned failure.")
