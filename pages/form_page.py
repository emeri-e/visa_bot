import pprint
import random
import time

from bs4 import BeautifulSoup
import urllib.parse

from utils.functions import create_session, extract_applicant
from utils.models import Browser
from .base import Page
from utils.functions import extract_json
from requests_toolbelt.multipart.encoder import MultipartEncoder


import json
import re


class FormPage(Page):
    url = None

    def __str__(self):
        return 'Form filing'

    def process(self, context):
        self.session = context['session']
        self.url = f"https://ita-pak.blsinternational.com/Global/BlsAppointment/VisaAppointmentForm?appointmentId={context['appointment_id']}"

        self.context = context
        response = self.session.get(self.url)

        html_response = response.text
        self.valid_fields = self.get_valid_fields(html_response)

        appointment_id = self._process_booking()

        if appointment_id:
            self.context['appointment_id'] = appointment_id
            return self.context
        

  
    def _process_booking(self):
        

        url = "https://ita-pak.blsinternational.com/Global/BLSAppointment/ManageAppointment"
        payload = self.valid_fields
        headers = {"Referer": self.context['Referer']}
        
        # payload['TotalAmount'] = ''
        # payload['ServerTravelDate'] = ''
        # payload['AppointmentNo'] = ''
        # payload['ImageId'] = ''
        # payload['ScriptData'] = ''

        # payload

        # with open('form.json', 'w') as f:
        #     json.dump(payload, f, indent=4)

        # payload = self.interactively_edit_payload(payload)

        # with open('form_edited.json', 'w') as f:
        #     json.dump(payload, f, indent=4)
        print("Submitting form...")
        response = self.session.post(url, data=payload, headers=headers)
        data = response.json()

        # response = self.session.get(self.url)
        # html_response = response.text
        # self.valid_fields = self.get_valid_fields(html_response)


        if data['success']:
            print("Form submitted!")
            return data['model']['Id']
        else:
            print("Appointment creation failed!")

    def interactively_edit_payload(self, payload):
        x = input("Do you want to edit the payload? (Press Enter to continue)")
        if not x:
            return payload
        
        print("\n--- Editing Payload ---")
        for key, value in payload.items():
            if isinstance(value, list):  # Handle nested lists like ApplicantsDetailsList
                print(f"\nEditing list: {key}")
                for i, item in enumerate(value):
                    print(f"Item {i + 1}: {item}")
                    for sub_key, sub_value in item.items():
                        new_value = input(f"Edit {sub_key} (current: {sub_value}): ").strip()
                        if new_value:
                            item[sub_key] = new_value
            else:
                new_value = input(f"Edit {key} (current: {value}): ").strip()
                if new_value:
                    payload[key] = new_value
        print("\nPayload editing complete.")
        return payload

    def get_valid_fields(self, page_text):
        soup = BeautifulSoup(page_text, 'html.parser')
        result = {}

        # Extract inputs and populate `result`
        for input_field in soup.find_all('input'):
            name = input_field.get('name')
            id = input_field.get('id')

            value = input_field.get('value', '')
            if name:
                result[name] = value
            elif id:
                id = id.split('_')[0]
                result[id] = value

        # Extract primary applicant data
        applicant_data = extract_applicant(page_text, 'primaryApplicant')

        dob = applicant_data['DateOfBirth'].split('T')[0]

        # Populate applicant details
        applicant = {
            "ApplicantSerialNo": "1",
            "FirstName": self.context['FirstName'],
            "LastName": self.context['LastName'],
            "SurName": self.context['SurName'],
            "SurnameAtBirth": self.context['SurName'],
            "ServerDateOfBirth": dob,
            "PlaceOfBirth": self.context['PlaceOfBirth'],
            "NationalityId": self.context['NationalityId'],
            "PassportType": applicant_data['PassportType'],
            "PassportNo": applicant_data['PassportNo'],
            "ServerPassportIssueDate": applicant_data['IssueDate'].split('T')[0],
            "ServerPassportExpiryDate": applicant_data['ExpiryDate'].split('T')[0],
            "IssuePlace": applicant_data['IssuePlace'],
            "IssueCountryId": applicant_data['IssueCountryId'],

            "ParentId": result['Id'],
            "ApplicantId": result['ApplicantId'],
            "Id": result['ApplicantId'],
            "CountryOfBirthId": self.context['CountryOfBirthId'],
            "NationalityAtBirthId": self.context['NationalityAtBirthId'],
            "GenderId": self.context['GenderId'],
            "MaritalStatusId": self.context['MaritalStatusId'],
            "HomeAddressLine1": "",
            "HasOtherResidenceship": 'false',
            "OtherResidenceshipPermitNumber": "",
            "OtherResidenceshipPermitValidUntill": None,
            "CurrentOccupationId": "",
            "PurposeOfJourneyId": "",
            "NumberOfEntriesRequested": "",
            "InvitingAddress": "",
            "ForeignNationalIdentityNumber": "",
            "InvitingContactName": "",
            "InvitingContactSurName": "",
            "InvitingAuthorityName": self.context['InvitingAuthorityName'],
            "MinorParentMobileNumber": "",
            "MinorParentEmail": "",
            "OtherCitizenFamilyRelationshipId": "",
            "InvitingContactCountryId": "",
            "InvitingContactFaxNo": "",
            "InvitingContactAddress": "",
            "InvitingContactContactNo": "",
            "InvitingContactEmail": "",
            "EmployerName": "",
            "EmployerAddress": "",
            "EmployerPhone": "",
            "EmployerEmail": "",
            "EmployerNationalIdentityNumber": "",
            "CompanyTaxIdentificationNumber": "",
            "EducationalEstablishmentName": "",
            "EducationalEstablishmentAddress": "",
            "EducationalEstablishmentPhone": "",
            "EducationalEstablishmentEmail": "",
            "MinorParentFirstName": "",
            "MinorParentAddress": "",
            "MinorParentForeignNationalIdentityNumber": ""
        }
        print("Applicant Details: ", applicant)
        # Prepare ApplicantsDetailsList
        applicants_details_list = [applicant]
        applicants_details_encoded = urllib.parse.quote(json.dumps(applicants_details_list))

        # Update the result dictionary
        result['ApplicantsDetailsList'] = applicants_details_encoded
        result['RemoveChildren'] = False
        result['ApplicantsNo'] = 1
        result['MinimumPassportValidityDays'] = 180
        result.pop('ApplicantId')

        # Remove empty fields
        result = {key: val for key, val in result.items() if val != ''}

        # Manually construct the payload to avoid double encoding
        payload = "&".join(
            f"{key}={val}" if key != "ApplicantsDetailsList" else f"{key}={val}"
            for key, val in result.items()
        )

        return payload

    def next(self):
        return 'payment_page'
    
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
    
    
    