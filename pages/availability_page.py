# import json
# import re
# import time

import datetime
import json
import random
from bs4 import BeautifulSoup

from utils.exceptions import EndException, LoginRedirectException
from utils.functions import extract_json
from .base import Page
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# from forms import AvailabilityForm
# from utils.captcha import fetch_captcha, solve_captcha
# from data import AVAILABILITY_FIELDS as context

class AvailabilityPage(Page):
    
    url = "https://ita-pak.blsinternational.com/Global/bls/VisaTypeVerification"
    captcha_data = {}
    valid_fields = {}

    def __str__(self):
        return "Checking Availability"
    
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

        # headers = {
        #     "requestverificationtoken": self.urvt
        # }

        response = self.session.post(url, caller='availability', headers=headers, data=payload)
        self.logger.info(f"{response.status_code} {response.text}") 
        data = response.json()

        slots = [slot['Name'] for slot in data if int(slot['Count']) > 0]

        return date, slots

    def process(self, context: dict) -> dict:
        if context.get('session'):
            self.session = context['session']
        else:
            raise Exception("[Availability Page]: No session provided in context")

        # print(f"[{str(self)}]: fetching page for captcha...")
        response = self.session.get(self.url)

        # if 'https://ita-pak.blsinternational.com/Global/account/Login?timeOut=True' in response.url:

        if response.status_code != 200:
            raise Exception(f"[{str(self)}]: Failed to load page, status code: {response.status_code}")

        self.context = context
        self.valid_fields = self.get_valid_fields(response.text)
        self.captcha_data = self.process_captcha(response.text, captcha_field_name='cd', use_local_ocr=context.get('local_ocr'))
        
        self.urvt = self.valid_fields['__RequestVerificationToken']
       
        payload = {
            'CaptchaData': self.captcha_data['captcha'],
            '__RequestVerificationToken': self.valid_fields['__RequestVerificationToken'],
            'X-Requested-With': 'XMLHttpRequest'
        }

        # print(f"[{str(self)}]: submitting payload...")
        post_response = self.session.post(self.url, data=payload)
        if post_response.status_code != 200:
            raise Exception(f"[{str(self)}]: POST request failed, status code: {post_response.status_code}")

        response_json = post_response.json()
        if response_json.get("success") == True:
            print(f"[{str(self)}]: Process successful!")
            return_url = response_json.get("returnUrl")
            context.update(returnUrl=return_url)

            referer_url = f"https://ita-pak.blsinternational.com{return_url}"
            headers = {"Referer": referer_url}

            r = self.session.get(referer_url)
            self.valid_fields = self.get_valid_fields(r.text)
            payload = self.get_payload(r.text, context['location'], context['visatype'], context['visasubtype'], context['category'])
            print(f"[{str(self)}]: Submitting payload: {payload}")
            payload.update({
                'CaptchaData': self.captcha_data['captcha'],
                'ScriptData': self.valid_fields['script_data'],
                '__RequestVerificationToken': self.valid_fields['__RequestVerificationToken']
            })

            r = self.session.post(referer_url, data=payload)
            data = r.json()

            if data.get("success"):
                print(f"[{str(self)}]: Available position found!. Details:{data}\n\n")
                return_url = data.get("returnUrl")
                
                self.context.update(returnUrl=return_url)
 
                return context
            else:

                response = self.session.get(self.url)
                if response.status_code != 200:
                    raise Exception(f"[{str(self)}]: Failed to load page, status code: {response.status_code}")

                self.context = context
                self.valid_fields = self.get_valid_fields(response.text)
                self.captcha_data = self.process_captcha(response.text, captcha_field_name='cd', use_local_ocr=context.get('local_ocr'))
                
                self.urvt = self.valid_fields['__RequestVerificationToken']
            
                payload = {
                    'CaptchaData': self.captcha_data['captcha'],
                    '__RequestVerificationToken': self.valid_fields['__RequestVerificationToken'],
                    'X-Requested-With': 'XMLHttpRequest'
                }

                post_response = self.session.post(self.url, data=payload)
                if post_response.status_code != 200:
                    raise Exception(f"[{str(self)}]: POST request failed, status code: {post_response.status_code}")

                response_json = post_response.json()
                if response_json.get("success") == True:
                    return_url = response_json.get("returnUrl")
                    context.update(returnUrl=return_url)

                    referer_url = f"https://ita-pak.blsinternational.com{return_url}"
                    headers = {"Referer": referer_url}

                    r = self.session.get(referer_url)
                    self.valid_fields = self.get_valid_fields(r.text)
                    payload2 = self.get_payload(r.text, context['location'], context['visatype'], context['visasubtype'], context['category'])
                    payload2.update({
                        'CaptchaData': self.captcha_data['captcha'],
                        'ScriptData': self.valid_fields['script_data'],
                        '__RequestVerificationToken': self.valid_fields['__RequestVerificationToken']
                    })
                





                print(f"[{str(self)}]: No available position found!, starting loop...")
                x = self.session.get(self.url)
                self.valid_fields = self.get_valid_fields(x.text)

                if context["range_selection"] == "Month":
                    # start_date = datetime.date.today() + datetime.timedelta(days=1)
                    start_date = datetime.datetime.strptime(context['date_selection'], "%Y-%m-%d").date()
                    end_date = start_date + datetime.timedelta(days=30)
                    dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days)]
                elif context["range_selection"] == "Week":
                    # start_date = datetime.date.today() + datetime.timedelta(days=1)
                    start_date = datetime.datetime.strptime(context['date_selection'], "%Y-%m-%d").date()
                    end_date = start_date + datetime.timedelta(days=7)
                    dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days)]
                else:
                    # dates = [context['date_selection'],]
                    start_date = datetime.date.today() + datetime.timedelta(days=1)
                    end_date = datetime.datetime.strptime(context['date_selection'], "%Y-%m-%d").date()
                    if end_date > start_date:
                        dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
                    else:
                        dates = [end_date,]  
                        
                context["allowed_dates"] = [date.strftime("%Y-%m-%d") if not isinstance(date, str) else date for date in dates ]
                choices = self.get_choices(context['location'], context['visatype'], context['visasubtype'], context['category'])

                start_time = time.time()

                while True:
                    random.shuffle(dates)
                    print(f"[{str(self)}]: Checking for available slots...")
                    available_date = None
                    
                    # Use ThreadPoolExecutor for concurrent slot checking
                    # with ThreadPoolExecutor(max_workers=5) as executor:
                    #     futures = {executor.submit(self._fetch_time_slots, date.strftime("%Y-%m-%d"), choices): date for date in dates}
                    #     for future in as_completed(futures):
                    #         date, slots = future.result()
                    #         if slots:  # If a slot is found
                    #             available_date = date
                    #             break
                    for date in dates:
                        if time.time() - start_time > 4 * 60:
                            raise LoginRedirectException(f"[{str(self)}]: Relogin")

                        date_str = date.strftime("%Y-%m-%d") if not isinstance(date, str) else date
                        try:
                            _,slots = self._fetch_time_slots(date_str, choices)
                        except:
                            self.logger.error('failed to fetch slot due to unavailablity')
                            continue
                        
                        if slots:
                            available_date = date
                            break
                        print(f"no slots found for {date}")
                        time.sleep(0.2)

        
                    if slots:
                        print(f"[{str(self)}]: Slots: {slots} found for {available_date},. proceeding...")
                        r = self.session.post(referer_url, data=payload2)
                        data = r.json()

                        if data.get("success"):
                            print(f"[{str(self)}]: Available position found!. Details:{data}\n\n")
                            return_url = data.get("returnUrl")
                            
                            self.context.update(returnUrl=return_url)
            
                            return context
                        break
                    else:
                        print(f"[{str(self)}]: No slots available, retrying after a wait...")
                        time.sleep(10)  # Wait before retrying

                return self.process(self.context)
        else:
            raise Exception(f"[{str(self)}]: Process failed with response: {response_json}")
    
    def next(self) -> str:
        return 'details_page'

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
        try:
            script_data = soup.find('input', {'id': 'ScriptData'})['value']
        except:
            script_data = None

        result['__RequestVerificationToken'] = token
        result['script_data'] = script_data

        return result
    
    


    def get_payload(self, page_text,location_name, visatype_name, visasubtype_name, category_name):
        """Retrieve the ID based on location, visa type, visa subtype, and category."""
        
        visa_data = extract_json(page_text, "visaIdData")
        location_data = extract_json(page_text, "locationData")
        visa_subtype_data = extract_json(page_text, "visasubIdData")
        category_data = extract_json(page_text, "AppointmentCategoryIdData")
        mission_data = extract_json(page_text, "missionData")
        
        # data = {
        #     "visaIdData": visa_data,
        #     "locationData": location_data,
        #     "visasubIdData": visa_subtype_data,
        #     "AppointmentCategoryIdData": category_data,
        #     "missionData": mission_data
        # }
        # with open('data.json', 'w') as f:
        #     json.dump(data, f, indent=4)

        location = next((loc for loc in location_data if loc["Name"] == location_name), None)
        if not location:
            return f"Location '{location_name}' not found."
        location_id = location["Id"]

        mission = next((m for m in mission_data if location_name in m["Name"]), None)
        if not mission:
            return f"mission for '{location_name}' not found."
        mission_id = mission["Id"]

        visa_type = next((visa for visa in visa_data if visa["Name"] == visatype_name and visa["LocationId"] == location_id), None)
        if not visa_type:
            return f"Visa type '{visatype_name}' with location '{location_name}' not found."
        visa_type_id = visa_type["Id"]

        visa_subtype = next((sub for sub in visa_subtype_data if sub["Name"] == visasubtype_name and sub["Value"] == visa_type_id), None)
        if not visa_subtype:
            return f"Visa subtype '{visasubtype_name}' not found."
        visa_subtype_id = visa_subtype["Id"]

        category = next((cat for cat in category_data if cat["Name"] == category_name), None)
        if not category:
            return f"Category '{category_name}' not found."
        category_id = category["Id"]



        visible_location_id = self.get_visible_id(page_text, "Location")
        visible_visatype_id = self.get_visible_id(page_text, "VisaType")
        visible_visasubtype_id = self.get_visible_id(page_text, "VisaSubType")
        visible_category_id = self.get_visible_id(page_text, "AppointmentCategoryId")
        # visible_appointment_for = get_visible_id(javascript_data, "AppointmentFor")
        self.context.update(
            choices = {
               'locationId': location_id,
               'missionId': mission_id,
               'visaType': visa_type_id,
               'visaSubType': visa_subtype_id,
               'categoryId': category_id,
               'applicantCount': 1
            }
        )
        
        return {
            "missionId": mission_id,
            f"Location{visible_location_id}": location_id,
            f"VisaType{visible_visatype_id}": visa_type_id,
            f"VisaSubType{visible_visasubtype_id}": visa_subtype_id,
            f"AppointmentCategoryId{visible_category_id}": category_id,
            f"AppointmentFor1": 'Individual',
            f"AppointmentFor2": 'Individual',
            f"AppointmentFor3": 'Individual',
            f"AppointmentFor4": 'Individual',
            f"AppointmentFor5": 'Individual',

        }

    def get_choices(self, location_name, visatype_name, visasubtype_name, category_name):
        with open('cache.html', 'r') as f:
            page_text = f.read()

        visa_data = extract_json(page_text, "visaIdData")
        location_data = extract_json(page_text, "locationData")
        visa_subtype_data = extract_json(page_text, "visasubIdData")
        category_data = extract_json(page_text, "AppointmentCategoryIdData")
        mission_data = extract_json(page_text, "missionData")
        
        location = next((loc for loc in location_data if loc["Name"] == location_name), None)
        if not location:
            return f"Location '{location_name}' not found."
        location_id = location["Id"]

        mission = next((m for m in mission_data if location_name in m["Name"]), None)
        if not mission:
            return f"mission for '{location_name}' not found."
        mission_id = mission["Id"]

        visa_type = next((visa for visa in visa_data if visa["Name"] == visatype_name and visa["LocationId"] == location_id), None)
        if not visa_type:
            return f"Visa type '{visatype_name}' with location '{location_name}' not found."
        visa_type_id = visa_type["Id"]

        visa_subtype = next((sub for sub in visa_subtype_data if sub["Name"] == visasubtype_name and sub["Value"] == visa_type_id), None)
        if not visa_subtype:
            return f"Visa subtype '{visasubtype_name}' not found."
        visa_subtype_id = visa_subtype["Id"]

        category = next((cat for cat in category_data if cat["Name"] == category_name), None)
        if not category:
            return f"Category '{category_name}' not found."
        category_id = category["Id"]

        choices = {
               'locationId': location_id,
               'missionId': mission_id,
               'visaType': visa_type_id,
               'visaSubType': visa_subtype_id,
               'categoryId': category_id,
               'applicantCount': 1
            }
        self.context.update(
            choices = choices
        )
        
        return choices

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

            divs = soup.find_all('div', class_='mb-3')
            valid_divs = []

            for div in divs:
                label = div.find('label') #, id=lambda x: x and item in x)
                if item not in div.prettify():
                    continue

                class_list = div.get('class', [])
                styled_classes = [cls for cls in class_list if cls in css_styles]

                for styled_class in styled_classes:
                    if 'display: block' in css_styles.get(styled_class, '') or  'display:block' in css_styles.get(styled_class, ''):
                        location_id = label.get('for')
                        if location_id and item in location_id:
                            valid_divs.append(location_id.replace(item, ''))
                        break

            return valid_divs[0]
    